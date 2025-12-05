"""
CloudContactAI A2P 10DLC Compliance Agent - API Server
Copyright (c) 2024 CloudContactAI, LLC. All rights reserved.

Main API server for A2P 10DLC compliance checking and campaign registration.
Provides endpoints for compliance analysis, data collection, and batch processing.
"""

# Load secrets from AWS Secrets Manager or .env file
try:
    from secrets_manager import load_secrets
    if not load_secrets():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
except ImportError:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    except ImportError:
        print("⚠️ python-dotenv not available, using system environment variables")

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from compliance_pipeline import A2PCompliancePipeline
from data_collection_agent import A2PDataCollectionAgent
from enhanced_compliance_strand import A2PComplianceStrand
from submission_tracker import SubmissionTracker
from cloudwatch_logger import CloudWatchLogger
from regulatory_verifier import RegulatoryVerifier
from readme_integration import ReadMeIntegration
import os
import re
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.getenv('ADMIN_PASSWORD', 'fallback-secret-key')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Enable CORS for frontend domains
CORS(app, 
     origins=[
         "https://agent.cloudcontactai.com",
         "https://main.d28k46xdno1z6x.amplifyapp.com",
         "https://d28k46xdno1z6x.amplifyapp.com",
         "http://localhost:3000",
         "http://localhost:5002",
         "http://127.0.0.1:3000",
         "http://127.0.0.1:5002"
     ],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "DELETE", "OPTIONS"])
pipeline = A2PCompliancePipeline()
data_agent = A2PDataCollectionAgent()
compliance_strand = A2PComplianceStrand()
tracker = SubmissionTracker()
logger = CloudWatchLogger()
regulatory_verifier = RegulatoryVerifier()
readme = ReadMeIntegration()

def get_client_ip():
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def verify_address_on_website(address, website_content, privacy_content, terms_content):
    """Verify address appears on website, privacy policy, or terms"""
    if not address:
        return False
    
    # Extract key parts of address for matching
    address_parts = []
    
    # Extract street number
    street_num = re.search(r'\b\d+\b', address)
    if street_num:
        address_parts.append(street_num.group())
    
    # Extract ZIP code
    zip_code = re.search(r'\b\d{5}(-\d{4})?\b', address)
    if zip_code:
        address_parts.append(zip_code.group())
    
    # Extract street name (remove common words)
    street_words = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 
                   'lane', 'ln', 'boulevard', 'blvd', 'parkway', 'pkwy', 'suite', 'ste']
    address_clean = address.lower()
    for word in street_words:
        address_clean = address_clean.replace(word, '')
    
    # Get significant words (3+ chars, not common words)
    words = [w.strip() for w in address_clean.split() if len(w.strip()) > 2 and w.strip().isalpha()]
    address_parts.extend(words[:2])  # Take first 2 significant words
    
    # Check all content sources
    all_content = ' '.join([
        website_content or '',
        privacy_content or '',
        terms_content or ''
    ]).lower()
    
    # Must find at least 2 address components
    matches = sum(1 for part in address_parts if part.lower() in all_content)
    return matches >= 2

@app.route('/api/verify-address', methods=['POST'])
def verify_address():
    """Verify address appears on website content"""
    try:
        data = request.get_json()
        address = data.get('street_address', '')
        
        # Get website content
        website_content = data.get('website_content', '')
        privacy_content = data.get('privacy_content', '')
        terms_content = data.get('terms_content', '')
        
        address_found = verify_address_on_website(
            address, website_content, privacy_content, terms_content
        )
        
        return jsonify({"address_found_on_website": address_found})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def validate_address(address):
    """Validate address format (street, city, state, zip)"""
    if not address or len(address.strip()) < 10:
        return False
    
    # Basic patterns for US addresses
    address_lower = address.lower().strip()
    
    # Check for basic components
    has_numbers = bool(re.search(r'\d+', address))  # Street number
    
    # Check for state (2-letter abbreviation OR full state name)
    state_abbreviations = r'\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)\b'
    state_names = r'\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming)\b'
    
    has_state = bool(re.search(state_abbreviations, address_lower)) or bool(re.search(state_names, address_lower))
    has_zip = bool(re.search(r'\b\d{5}(-\d{4})?\b', address))  # 5 or 9 digit zip
    
    # Check for common address words
    street_words = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 
                   'lane', 'ln', 'boulevard', 'blvd', 'parkway', 'pkwy', 'suite', 'ste']
    has_street_word = any(word in address_lower for word in street_words)
    
    # Must have numbers, state, zip, and either street word or be long enough
    return has_numbers and has_state and has_zip and (has_street_word or len(address) > 25)

def validate_ein(ein):
    """Validate EIN format (XX-XXXXXXX)"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', ein)
    # EIN should be exactly 9 digits
    return len(digits) == 9

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    # Check if it's 10 or 11 digits (US format)
    return len(digits) in [10, 11]

def check_email_domain_match(email, website):
    """Check if email domain matches website domain"""
    try:
        email_domain = email.split('@')[1].lower()
        website_domain = urlparse(website).netloc.lower()
        
        # Remove www. prefix if present
        if website_domain.startswith('www.'):
            website_domain = website_domain[4:]
            
        return email_domain == website_domain
    except:
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancer"""
    return jsonify({"status": "healthy", "service": "a2p-compliance-agent"})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "a2p-compliance-pipeline"})

@app.route('/api/validate-data', methods=['POST'])
def validate_data():
    """Validate submission data"""
    try:
        data = request.get_json()
        validation_results = {}
        
        # Validate EIN
        ein = data.get('company_ein', '')
        if ein:
            validation_results['ein_valid'] = validate_ein(ein)
        
        # Validate address
        address = data.get('street_address', '')
        if address:
            validation_results['address_valid'] = validate_address(address)
        
        # Validate email
        email = data.get('support_email', '')
        if email:
            validation_results['email_valid'] = validate_email(email)
            validation_results['email_domain_match'] = check_email_domain_match(
                email, data.get('brand_website', '')
            )
        
        # Validate phone
        phone = data.get('support_phone', '')
        if phone:
            validation_results['phone_valid'] = validate_phone(phone)
        
        return jsonify(validation_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape-website', methods=['POST'])
def scrape_website():
    """Scrape a website and return structured data"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
            
        website_data = data_agent.scrape_website(url)
        compliance_analysis = data_agent.analyze_website_compliance(website_data)
        
        return jsonify({
            "website_data": website_data,
            "compliance_analysis": compliance_analysis
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-submission', methods=['POST'])
def analyze_submission():
    """Analyze a complete A2P submission and store results"""
    client_ip = get_client_ip()
    session_id = logger.get_session_id(client_ip)
    
    try:
        submission_data = request.get_json()
        
        # Log session start
        logger.log_session_start(client_ip, submission_data)
        print(f"Session {session_id}: Received submission from {client_ip}")
        
        # Generate submission package with scraping
        print("Starting website scraping...")
        try:
            submission_package = data_agent.generate_submission_package(submission_data)
            logger.log_website_scraping(session_id, submission_data.get('brand_website', ''), True)
            print("Website scraping completed")
        except Exception as scrape_error:
            logger.log_website_scraping(session_id, submission_data.get('brand_website', ''), False, str(scrape_error))
            logger.log_error(session_id, "website_scraping", str(scrape_error))
            raise scrape_error
        
        # Run compliance check
        print("Running compliance check...")
        try:
            compliance_result = pipeline.compliance_agent.process_communication(submission_package)
            
            # Add website compliance analysis to result
            if 'compliance_analysis' in submission_package:
                compliance_result['compliance_analysis'] = submission_package['compliance_analysis']
            
            # Run business verification
            print("Running regulatory verification...")
            business_verification = regulatory_verifier.verify_business(submission_data)
            
            # Adjust score based on regulatory verification
            if business_verification.get('issues_found', False):
                score_adjustment = regulatory_verifier.get_risk_score_adjustment(business_verification)
                compliance_result['score'] = max(0, compliance_result.get('score', 0) + score_adjustment)
                
                # Add regulatory issues to violations
                business_issues = business_verification.get('issues', [])
                for issue in business_issues:
                    compliance_result.setdefault('violations', []).append(f"Regulatory Check: {issue}")
                
                print(f"Regulatory verification found {len(business_issues)} issues, score adjusted by {score_adjustment}")
            
            # Add verification results to compliance result
            compliance_result['business_verification'] = business_verification
            
            logger.log_compliance_result(session_id, compliance_result)
            print("Compliance check completed")
        except Exception as compliance_error:
            logger.log_error(session_id, "compliance_analysis", str(compliance_error))
            raise compliance_error
        
        # Store in DynamoDB
        try:
            submission_id = tracker.store_submission(client_ip, submission_data, compliance_result)
            print(f"Stored submission {submission_id} for session {session_id}")
        except Exception as e:
            logger.log_error(session_id, "dynamodb_storage", str(e))
            print(f"Failed to store submission: {e}")
        
        # Generate final recommendation
        recommendation = pipeline._generate_final_recommendation(compliance_result)
        user_stats = tracker.get_submission_stats(client_ip)
        
        return jsonify({
            "submission_package": submission_package,
            "compliance_result": compliance_result,
            "recommendation": recommendation,
            "submission_id": submission_id if 'submission_id' in locals() else None,
            "user_stats": user_stats,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.log_error(session_id, "analyze_submission", str(e), {
            "brand_name": submission_data.get('brand_name') if 'submission_data' in locals() else None,
            "brand_website": submission_data.get('brand_website') if 'submission_data' in locals() else None
        })
        print(f"Session {session_id}: Error in analyze_submission: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}", "session_id": session_id}), 500

@app.route('/api/compliance/check', methods=['POST'])
def strand_compliance_check():
    """Enhanced compliance check using strand"""
    try:
        submission_data = request.get_json()
        result = compliance_strand.process_submission(submission_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compliance/batch-messages', methods=['POST'])
def strand_batch_messages():
    """Validate batch of messages with strand"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        context = data.get('context', {})
        
        result = compliance_strand.validate_message_batch(messages, context)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compliance/recommendations', methods=['POST'])
def strand_recommendations():
    """Get compliance recommendations using strand"""
    try:
        submission_data = request.get_json()
        result = compliance_strand.get_compliance_recommendations(submission_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with A2P 10DLC Compliance expert via LLM"""
    client_ip = get_client_ip()
    session_id = logger.get_session_id(client_ip)
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Try to use OpenAI if available
        try:
            import openai
            import os
            
            # A2P expert system prompt
            system_prompt = """You are an A2P 10DLC Compliance Expert with deep knowledge of:
- A2P (Application-to-Person) messaging compliance
- 10DLC (10-Digit Long Code) registration requirements
- TCPA (Telephone Consumer Protection Act) regulations
- FDCPA (Fair Debt Collection Practices Act) compliance
- CFPB (Consumer Financial Protection Bureau) guidelines
- Carrier compliance requirements (Verizon, AT&T, T-Mobile)
- Message content analysis and optimization
- Brand registration and campaign approval processes

You are professional, knowledgeable, and focused on compliance best practices. 
Answer questions about A2P compliance, but also guide users to start their formal compliance analysis by typing 'start' when appropriate.
Keep responses concise and actionable."""

            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            llm_response = response.choices[0].message.content
            
        except ImportError:
            # OpenAI not installed - use fallback responses
            print("OpenAI not available, using fallback responses")
            llm_response = get_fallback_response(user_message)
            
        except Exception as llm_error:
            # OpenAI error - use fallback
            print(f"LLM error: {llm_error}")
            logger.log_error(session_id, "llm_chat", str(llm_error))
            llm_response = get_fallback_response(user_message)
        
        # Log chat interaction
        logger.log_chat_interaction(session_id, user_message, llm_response)
        
        return jsonify({
            "response": llm_response,
            "user_message": user_message,
            "session_id": session_id
        })
        
    except Exception as e:
        logger.log_error(session_id, "chat_endpoint", str(e))
        print(f"Chat error: {e}")
        return jsonify({
            "response": "I'm your A2P 10DLC compliance expert. Type 'start' to begin your compliance analysis or ask me about A2P regulations.",
            "error": str(e),
            "session_id": session_id
        }), 200

def get_fallback_response(user_message):
    """Fallback responses when OpenAI is not available"""
    message_lower = user_message.lower()
    
    if any(term in message_lower for term in ['10dlc', '10-dlc', 'ten dlc']):
        return "10DLC registration is required for business messaging. I can help analyze your compliance setup. Type 'start' to begin your submission."
    elif any(term in message_lower for term in ['tcpa', 'consent', 'opt-in']):
        return "TCPA requires proper consent and opt-out mechanisms. I can review your opt-in processes. Type 'start' for analysis."
    elif any(term in message_lower for term in ['fdcpa', 'debt', 'collection']):
        return "FDCPA has strict rules for debt collection messaging. I can analyze your compliance. Type 'start' to begin."
    elif any(term in message_lower for term in ['help', 'what', 'how']):
        return "I'm an A2P 10DLC compliance expert. I analyze messaging campaigns for regulatory compliance. Type 'start' to begin."
    else:
        return "I can help with A2P compliance questions and analyze your messaging setup. Type 'start' to begin your compliance review."

@app.route('/api/developer-help', methods=['POST', 'OPTIONS'])
def developer_help():
    """Answer developer documentation questions using ReadMe"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Search ReadMe documentation
        results = readme.search_docs(query)
        answer = readme.format_answer(results, query)
        
        return jsonify({
            "answer": answer,
            "query": query,
            "results_count": len(results)
        })
        
    except Exception as e:
        print(f"Developer help error: {e}")
        return jsonify({
            "answer": "I'm having trouble accessing the documentation right now. Please visit https://developer.cloudcontactai.com directly.",
            "error": str(e)
        }), 200

@app.route('/api/user/history', methods=['GET'])
def get_user_history():
    """Get submission history for current user"""
    try:
        client_ip = get_client_ip()
        submissions = tracker.get_user_submissions(client_ip)
        stats = tracker.get_submission_stats(client_ip)
        
        return jsonify({
            "submissions": submissions,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get user statistics"""
    try:
        client_ip = get_client_ip()
        stats = tracker.get_submission_stats(client_ip)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Admin API endpoints

@app.route('/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    """Admin login API"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASSWORD'):
            # Generate simple token
            import hashlib
            token = hashlib.sha256(f"{username}:{password}:{app.secret_key}".encode()).hexdigest()
            return jsonify({"success": True, "token": token})
        
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/submissions', methods=['GET'])
def admin_get_submissions():
    """Get all submissions for admin"""
    # Check for token in Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # Verify token
        import hashlib
        expected_token = hashlib.sha256(
            f"{os.getenv('ADMIN_USER')}:{os.getenv('ADMIN_PASSWORD')}:{app.secret_key}".encode()
        ).hexdigest()
        if token == expected_token:
            try:
                submissions = tracker.get_all_submissions()
                return jsonify({"submissions": submissions})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Not authenticated"}), 401

@app.route('/admin/generate-clean-site/<submission_id>', methods=['POST'])
def admin_generate_clean_site(submission_id):
    """Generate cleaned website without debt content"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        import hashlib
        expected_token = hashlib.sha256(
            f"{os.getenv('ADMIN_USER')}:{os.getenv('ADMIN_PASSWORD')}:{app.secret_key}".encode()
        ).hexdigest()
        if token == expected_token:
            try:
                # Check if site already generated
                submission = tracker.get_submission_by_id(submission_id)
                if submission and submission.get('generated_site_url'):
                    return jsonify({
                        "success": True, 
                        "url": submission['generated_site_url'],
                        "message": "Site already generated"
                    })
                
                from site_generator import CleanSiteGenerator
                generator = CleanSiteGenerator()
                url = generator.generate_clean_site(submission_id, tracker)
                
                # Save the URL to DynamoDB
                tracker.update_generated_site_url(submission_id, url)
                
                return jsonify({"success": True, "url": url})
            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Not authenticated"}), 401

@app.route('/admin/submissions/<submission_id>', methods=['DELETE'])
def admin_delete_submission(submission_id):
    """Delete a submission"""
    # Check for token in Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # Verify token
        import hashlib
        expected_token = hashlib.sha256(
            f"{os.getenv('ADMIN_USER')}:{os.getenv('ADMIN_PASSWORD')}:{app.secret_key}".encode()
        ).hexdigest()
        if token == expected_token:
            try:
                tracker.delete_submission(submission_id)
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Not authenticated"}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout API"""
    session.pop('admin_logged_in', None)
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
