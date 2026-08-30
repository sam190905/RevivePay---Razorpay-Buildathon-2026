"""AI Agent for failed payment diagnosis and recommendation."""

import logging
import json
from openai import AsyncOpenAI
from pydantic import ValidationError

from app.config import settings
from app.models.payment import Payment
from app.models.customer import Customer
from app.schemas.recovery import AIDiagnosisResult, RecoveryActionType

logger = logging.getLogger(__name__)

class AIAgentError(Exception):
    pass

class AIRecoveryAgent:
    """AI agent that diagnoses failures and recommends a recovery action."""

    def __init__(self):
        # Allow disabling AI in tests via a dummy key or setting
        self.api_key = settings.openai_api_key
        # For a real implementation, you would use AsyncOpenAI(api_key=self.api_key)
        # But if the key is "sk-mock-key" we know it's a test/mock environment.
        self.is_mock = self.api_key == "sk-mock-key" or not self.api_key
        if not self.is_mock:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    def _build_prompt(self, payment: Payment, customer: Customer) -> str:
        """Construct the prompt with relevant context."""
        return f"""
You are an expert payment recovery AI.
A payment has failed. Analyze the context and provide a structured diagnosis.

Context:
- Amount: {payment.amount} (in smallest currency unit, e.g. paise)
- Currency: {payment.currency}
- Razorpay Error Code: {payment.failure_code}
- Razorpay Error Reason: {payment.failure_reason}
- Customer Email: {customer.email}

Your allowed recovery actions are: {", ".join([a.value for a in RecoveryActionType])}

Instructions:
1. Classify the failure (e.g. temporary_failure, insufficient_funds, fraud, etc).
2. Recommend the best recovery action from the allowed list.
3. Provide your confidence score (0.0 to 1.0).
4. Provide a concise reason.
"""

    async def diagnose_failure(self, payment: Payment, customer: Customer) -> AIDiagnosisResult:
        """Call the LLM to get a structured diagnosis."""
        logger.info(f"AI Agent diagnosing payment {payment.id}")
        
        if self.is_mock:
            logger.info("Using mock AI diagnosis (mock key detected)")
            return self._mock_diagnose(payment)
            
        prompt = self._build_prompt(payment, customer)
        
        try:
            # Using structured outputs for reliable JSON parsing
            response = await self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a deterministic payment recovery assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format=AIDiagnosisResult,
            )
            
            result = response.choices[0].message.parsed
            if not result:
                raise AIAgentError("Model returned empty parsed result")
                
            logger.info(f"AI diagnosis successful: {result.classification} ({result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"AI Agent failed to diagnose: {e}")
            raise AIAgentError(f"LLM failed: {e}")

    def _mock_diagnose(self, payment: Payment) -> AIDiagnosisResult:
        """Deterministic mock for tests/demo when API key is missing."""
        code = (payment.failure_code or "").upper()
        if code == "FRAUD":
            return AIDiagnosisResult(
                classification="fraud",
                confidence=0.99,
                recommended_action=RecoveryActionType.MANUAL_REVIEW,
                reason="High confidence of fraudulent activity based on error code."
            )
        elif code == "GATEWAY_ERROR":
            return AIDiagnosisResult(
                classification="temporary_failure",
                confidence=0.85,
                recommended_action=RecoveryActionType.CREATE_PAYMENT_LINK,
                reason="Gateway timeout is likely a temporary failure."
            )
        else:
            return AIDiagnosisResult(
                classification="insufficient_funds",
                confidence=0.70,
                recommended_action=RecoveryActionType.CREATE_PAYMENT_LINK,
                reason="Standard payment failure, suggesting retry via payment link."
            )

ai_agent = AIRecoveryAgent()
