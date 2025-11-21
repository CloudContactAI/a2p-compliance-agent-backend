# CCAI Collections Compliance Agent

An AgentCore Strand solution for automated compliance checking of debt collection communications based on CCAI Collections Compliance requirements.

## Features

- **TCPA Compliance**: Consent verification, opt-out mechanisms, time restrictions
- **FDCPA Compliance**: Debt validation, harassment prevention, third-party disclosure rules
- **CFPB Compliance**: Consumer protection, fair practices, dispute resolution

## Quick Start

1. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run example:
```bash
source venv/bin/activate
python3 example_usage.py
```

3. Start API server:
```bash
source venv/bin/activate
python3 api.py
```

## API Endpoints

### Check Single Communication
```bash
POST /compliance/check
Content-Type: application/json

{
  "content": "Your debt collection message...",
  "consent_obtained": true,
  "opt_out_available": true,
  "time_sent": "14:30",
  "debt_validation_notice": true,
  "harassment_indicators": false,
  "third_party_disclosure": false,
  "consumer_protection_measures": true,
  "unfair_practices": false
}
```

### Batch Processing
```bash
POST /compliance/batch
Content-Type: application/json

{
  "communications": [
    { /* communication 1 */ },
    { /* communication 2 */ }
  ]
}
```

## Architecture

- `agent_core.py`: Core compliance logic and rule engine
- `compliance_strand.py`: Strand interface for processing communications
- `api.py`: REST API interface
- `example_usage.py`: Usage examples and testing

## Compliance Rules

The agent evaluates communications against:
- TCPA requirements for consent and timing
- FDCPA debt collection practices
- CFPB consumer protection standards

## Response Format

```json
{
  "status": "compliant|non_compliant|requires_review",
  "violations": ["list of violations"],
  "recommendations": ["list of recommendations"],
  "confidence_score": 0.85,
  "compliant": true
}
```
