import asyncio
import os
from app.config import settings
from app.services.ai_agent import ai_agent
from app.models.payment import Payment
from app.models.customer import Customer

async def run_test():
    print(f"Provider: {settings.ai_provider}")
    print(f"Model: {settings.gemini_model}")
    print(f"API Key Starts With: {settings.gemini_api_key[:5]}... (length: {len(settings.gemini_api_key)})")
    
    # Check fallback availability
    fallback_available = getattr(ai_agent, "_mock_diagnose", None) is not None
    print(f"Fallback available: {fallback_available}")

    print("\nStarting AI diagnosis test...")
    payment = Payment(
        id="test-123",
        amount=50000,
        currency="INR",
        failure_code="INSUFFICIENT_FUNDS",
        failure_reason="Customer account has insufficient balance"
    )
    customer = Customer(
        email="test@example.com"
    )

    try:
        result = await ai_agent.diagnose_failure(payment, customer)
        print("\nAPI connectivity: Success")
        print("Structured output: Valid AIDiagnosisResult parsed successfully")
        print(f"  -> Classification: {result.classification}")
        print(f"  -> Confidence: {result.confidence}")
        print(f"  -> Recommended Action: {result.recommended_action.value}")
        print(f"  -> Reason: {result.reason}")
    except Exception as e:
        print(f"\nAPI connectivity: Failed")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
