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
        self.provider = settings.ai_provider.lower()
        if self.provider == "gemini":
            self.api_key = settings.gemini_api_key
            self.model = settings.gemini_model
        else:
            self.api_key = settings.openai_api_key
            self.model = settings.openai_model

        # Allow disabling AI in tests via a dummy key, empty key, or developer mode
        self.is_mock = self.api_key == "sk-mock-key" or not self.api_key or settings.app_mode == "developer"
        
        self.openai_client = None
        self.gemini_client = None
        
        if not self.is_mock:
            if self.provider == "gemini":
                from google import genai
                self.gemini_client = genai.Client(api_key=self.api_key)
            else:
                self.openai_client = AsyncOpenAI(api_key=self.api_key)

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
2. You may only select from the currently executable recovery actions:
{", ".join([a.value for a in RecoveryActionType])}
3. Provide your confidence score (0.0 to 1.0).
4. Provide a concise reason.
"""

    async def diagnose_failure(self, payment: Payment, customer: Customer) -> AIDiagnosisResult:
        """Call the LLM to get a structured diagnosis."""
        logger.info(f"AI Agent diagnosing payment {payment.id} via {self.provider}")
        
        if self.is_mock:
            logger.info("Using mock AI diagnosis (mock key detected or missing)")
            return self._mock_diagnose(payment)
            
        prompt = self._build_prompt(payment, customer)
        
        try:
            if self.provider == "gemini":
                from google.genai import types
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a deterministic payment recovery assistant.",
                        response_mime_type="application/json",
                        response_schema=AIDiagnosisResult,
                    ),
                )
                
                if not response.text:
                    raise AIAgentError("Model returned empty result")
                    
                result = AIDiagnosisResult.model_validate_json(response.text)
                logger.info(f"AI diagnosis successful (Gemini): {result.classification} ({result.confidence})")
                return result
                
            else:
                # Using structured outputs for reliable JSON parsing
                response = await self.openai_client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a deterministic payment recovery assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=AIDiagnosisResult,
                )
                
                result = response.choices[0].message.parsed
                if not result:
                    raise AIAgentError("Model returned empty parsed result")
                    
                logger.info(f"AI diagnosis successful (OpenAI): {result.classification} ({result.confidence})")
                return result
            
        except Exception as e:
            logger.error(f"AI Agent failed to diagnose: {e}")
            raise AIAgentError(f"LLM failed: {e}")

    def _mock_diagnose(self, payment: Payment) -> AIDiagnosisResult:
        """Deterministic mock for tests/demo when API key is missing."""
        code = (payment.failure_code or "").upper()
        reason = payment.failure_reason or payment.failure_code or "unknown"
        
        if code == "FRAUD":
            return AIDiagnosisResult(
                classification=reason,
                confidence=0.95,
                recommended_action=RecoveryActionType.MANUAL_REVIEW,
                reason="High confidence of fraudulent activity based on error code."
            )
        elif code == "GATEWAY_ERROR":
            return AIDiagnosisResult(
                classification=reason,
                confidence=0.85,
                recommended_action=RecoveryActionType.CREATE_PAYMENT_LINK,
                reason="Gateway timeout is likely a temporary failure."
            )
        else:
            return AIDiagnosisResult(
                classification=reason,
                confidence=0.85,
                recommended_action=RecoveryActionType.CREATE_PAYMENT_LINK,
                reason="Standard payment failure, suggesting retry via payment link."
            )

ai_agent = AIRecoveryAgent()
