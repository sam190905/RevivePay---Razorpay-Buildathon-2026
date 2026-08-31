import json
from app.schemas.recovery import RecoveryActionType, AIDiagnosisResult
from app.services.ai_agent import AIRecoveryAgent
from app.config import settings
from app.models.payment import Payment
from app.models.customer import Customer

def inspect_runtime():
    print("--- ACTIVE RecoveryActionType ---")
    print(list(RecoveryActionType))
    
    print("\n--- ACTIVE AIDiagnosisResult ---")
    schema = AIDiagnosisResult.model_json_schema()
    print(json.dumps(schema, indent=2))
    
    print("\n--- ACTIVE GEMINI PROMPT ACTIONS ---")
    agent = AIRecoveryAgent()
    # Dummy objects
    p = Payment(amount=1000, currency="INR", failure_code="ERR", failure_reason="Test")
    c = Customer(email="test@example.com")
    prompt = agent._build_prompt(p, c)
    print(prompt)
    
    print("\n--- RUNNING PROCESS SOURCE / ENV ---")
    print(f"APP_MODE: {settings.app_mode}")
    print(f"AI_PROVIDER: {settings.ai_provider}")
    print(f"GEMINI_MODEL: {settings.gemini_model}")
    print(f"File location for AIAgent: {AIRecoveryAgent.__module__}")
    print(f"File location for RecoveryActionType: {RecoveryActionType.__module__}")

if __name__ == "__main__":
    inspect_runtime()
