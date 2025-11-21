"""
Complete A2P Compliance Pipeline
Combines data collection, website scraping, and compliance checking
"""

from typing import Dict
from data_collection_agent import A2PDataCollectionAgent
from compliance_strand import ComplianceStrand
import json

class A2PCompliancePipeline:
    def __init__(self):
        self.data_agent = A2PDataCollectionAgent()
        self.compliance_agent = ComplianceStrand()
        
    def run_full_pipeline(self, interactive: bool = True) -> Dict:
        """Run complete pipeline from data collection to compliance check"""
        
        if interactive:
            # Interactive data collection
            submission_data = self.data_agent.collect_submission_data()
            submission_package = self.data_agent.generate_submission_package(submission_data)
        else:
            # Use provided data (for API/batch processing)
            submission_package = submission_data
            
        # Run compliance check
        compliance_result = self.compliance_agent.process_communication(submission_package)
        
        # Combine results
        final_result = {
            'submission_data': submission_package,
            'compliance_result': compliance_result,
            'recommendation': self._generate_final_recommendation(compliance_result)
        }
        
        return final_result
    
    def _generate_final_recommendation(self, compliance_result: Dict) -> Dict:
        """Generate final recommendation for submission"""
        score = compliance_result.get('score', 0)
        status = compliance_result.get('status', 'rejection_likely')
        
        if status == 'approvable' and score >= 99:
            recommendation = {
                'action': 'SUBMIT',
                'confidence': 'HIGH',
                'message': 'Campaign meets all compliance requirements and is ready for submission.'
            }
        elif score >= 90:
            recommendation = {
                'action': 'REVIEW_AND_FIX',
                'confidence': 'MEDIUM', 
                'message': 'Campaign has minor issues that should be addressed before submission.'
            }
        else:
            recommendation = {
                'action': 'DO_NOT_SUBMIT',
                'confidence': 'HIGH',
                'message': 'Campaign has critical compliance issues and will likely be rejected.'
            }
            
        return recommendation
    
    def generate_report(self, pipeline_result: Dict) -> str:
        """Generate human-readable compliance report"""
        submission = pipeline_result['submission_data']
        compliance = pipeline_result['compliance_result']
        recommendation = pipeline_result['recommendation']
        
        report = f"""
A2P COMPLIANCE REPORT
{'='*50}

BRAND INFORMATION:
• Brand Name: {submission['brand_name']}
• Website: {submission['brand_website']}
• Use Case: {submission['use_case']}

COMPLIANCE ASSESSMENT:
• Status: {compliance['status'].upper()}
• Score: {compliance['score']}/100
• Confidence: {compliance['confidence_score']}

FINAL RECOMMENDATION: {recommendation['action']}
{recommendation['message']}

"""
        
        if compliance['violations']:
            report += "VIOLATIONS FOUND:\n"
            for violation in compliance['violations']:
                report += f"• {violation}\n"
            report += "\n"
            
        if compliance['recommendations']:
            report += "RECOMMENDED ACTIONS:\n"
            for rec in compliance['recommendations']:
                report += f"• {rec}\n"
            report += "\n"
                
        # Website analysis
        if 'compliance_analysis' in submission:
            analysis = submission['compliance_analysis']
            report += f"WEBSITE RISK LEVEL: {analysis['risk_level']}\n"
            if analysis['compliance_issues']:
                report += "WEBSITE ISSUES:\n"
                for issue in analysis['compliance_issues']:
                    report += f"• {issue}\n"
        
        return report

def main():
    pipeline = A2PCompliancePipeline()
    
    print("🚀 Starting A2P Compliance Pipeline...")
    
    # Run full pipeline
    result = pipeline.run_full_pipeline(interactive=True)
    
    # Generate and display report
    report = pipeline.generate_report(result)
    print(report)
    
    # Save results
    with open('compliance_report.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("📄 Full results saved to compliance_report.json")
    
    return result

if __name__ == "__main__":
    main()
