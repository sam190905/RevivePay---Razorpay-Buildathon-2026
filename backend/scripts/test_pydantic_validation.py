import asyncio
import json
from app.schemas.recovery import AIDiagnosisResult
from pydantic import ValidationError

def test():
    fake_json = json.dumps({
        "classification": "temporary_failure",
        "confidence": 0.9,
        "recommended_action": "retry_payment",
        "reason": "Test"
    })
    
    try:
        res = AIDiagnosisResult.model_validate_json(fake_json)
        print("SUCCESS:", res)
    except ValidationError as e:
        print("VALIDATION ERROR:", e)

if __name__ == "__main__":
    test()
