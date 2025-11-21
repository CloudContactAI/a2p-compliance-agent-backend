"""
Enhanced A2P Compliance Strand
Provides advanced compliance checking with context awareness
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from agent_core import CCaiComplianceAgent
from compliance_pipeline import A2PCompliancePipeline

class A2PComplianceStrand:
    def __init__(self):
        self.pipeline = A2PCompliancePipeline()
        self.session_context = {}
        
    def process_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete A2P submission with context"""
        try:
            # Store context for this session
            self.session_context = {
                'brand_name': submission_data.get('brand_name'),
                'vertical': submission_data.get('vertical'),
                'use_case': submission_data.get('use_case'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Run full pipeline analysis
            result = self.pipeline.compliance_agent.process_communication(submission_data)
            
            # Add strand-specific metadata
            result.update({
                'strand_version': '2.0',
                'processing_time': datetime.now().isoformat(),
                'context': self.session_context
            })
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "compliant": False,
                "score": 0,
                "strand_version": "2.0"
            }
    
    def validate_message_batch(self, messages: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate batch of messages with shared context"""
        results = []
        
        for i, message in enumerate(messages):
            message_data = {
                'content': message,
                'message_id': f"msg_{i+1}",
                **context
            }
            
            result = self.pipeline.compliance_agent.process_communication(message_data)
            result['message_index'] = i + 1
            results.append(result)
        
        return {
            'batch_results': results,
            'summary': self._generate_batch_summary(results),
            'context': context
        }
    
    def get_compliance_recommendations(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific recommendations for improving compliance"""
        result = self.process_submission(submission_data)
        
        recommendations = {
            'critical_fixes': [],
            'suggested_improvements': [],
            'best_practices': []
        }
        
        # Categorize recommendations by priority
        for rec in result.get('recommendations', []):
            if 'required' in rec.lower() or 'must' in rec.lower():
                recommendations['critical_fixes'].append(rec)
            elif 'should' in rec.lower() or 'recommend' in rec.lower():
                recommendations['suggested_improvements'].append(rec)
            else:
                recommendations['best_practices'].append(rec)
        
        return {
            'compliance_score': result.get('score', 0),
            'status': result.get('status'),
            'recommendations': recommendations,
            'violations': result.get('violations', [])
        }
    
    def _generate_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary for batch processing"""
        total = len(results)
        compliant = sum(1 for r in results if r.get('compliant', False))
        avg_score = sum(r.get('score', 0) for r in results) / total if total > 0 else 0
        
        return {
            'total_messages': total,
            'compliant_messages': compliant,
            'compliance_rate': round(compliant / total * 100, 2) if total > 0 else 0,
            'average_score': round(avg_score, 1),
            'recommendation': 'approved' if avg_score >= 80 else 'needs_review'
        }
