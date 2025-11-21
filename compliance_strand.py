"""
CCAI Collections Compliance Strand Interface
Provides the main entry point for compliance checking
"""

from typing import Dict, Any, List
import json
from agent_core import CCaiComplianceAgent, ComplianceResult

class ComplianceStrand:
    def __init__(self):
        self.agent = CCaiComplianceAgent()
        
    def process_communication(self, communication: Dict[str, Any]) -> Dict[str, Any]:
        """Process a communication for compliance"""
        try:
            result = self.agent.evaluate_compliance(communication)
            
            return {
                "status": result.status.value,
                "violations": result.violations,
                "recommendations": result.recommendations,
                "confidence_score": result.confidence_score,
                "score": result.score,
                "compliant": result.status.value == "approvable",
                "rules_version": self.agent.rules_version
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "compliant": False,
                "score": 0
            }
    
    def batch_process(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple communications"""
        results = []
        for comm in communications:
            result = self.process_communication(comm)
            result["communication_id"] = comm.get("id", "unknown")
            results.append(result)
        return results
    
    def get_compliance_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate compliance summary from results"""
        total = len(results)
        approvable = sum(1 for r in results if r.get("compliant", False))
        
        violation_counts = {}
        avg_score = sum(r.get("score", 0) for r in results) / total if total > 0 else 0
        
        for result in results:
            for violation in result.get("violations", []):
                section = violation.split(":")[0]
                violation_counts[section] = violation_counts.get(section, 0) + 1
        
        return {
            "total_communications": total,
            "approvable_count": approvable,
            "rejection_likely_count": total - approvable,
            "approval_rate": round(approvable / total * 100, 2) if total > 0 else 0,
            "average_score": round(avg_score, 1),
            "common_violations": violation_counts
        }
