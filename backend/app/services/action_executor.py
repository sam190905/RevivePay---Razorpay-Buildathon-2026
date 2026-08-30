"""Action execution abstraction."""

import logging
from typing import Any
from app.schemas.recovery import RecoveryActionType
from app.integrations.razorpay_client import razorpay_client, RazorpayClientError
from app.models.customer import Customer
from app.models.payment import Payment

from app.config import settings
import uuid
import httpx

logger = logging.getLogger(__name__)

class ActionExecutionError(Exception):
    """Raised when an action execution fails."""
    pass

class ActionExecutor:
    """Executes deterministic recovery actions via integrations."""

    async def execute(self, action_type: RecoveryActionType, payment: Payment, customer: Customer) -> dict[str, Any]:
        """
        Execute the specified recovery action.
        
        Returns:
            dict containing status, result payload, and any errors.
        """
        logger.info(f"Executing action {action_type} for payment {payment.id} (demo_mode={settings.demo_mode})")
        
        if action_type == RecoveryActionType.CREATE_PAYMENT_LINK:
            return await self._create_payment_link(payment, customer)
        elif action_type == RecoveryActionType.MANUAL_REVIEW:
            return {"status": "success", "result": "Routed to manual review queue.", "is_simulated": settings.demo_mode}
        else:
            raise ActionExecutionError(f"Unsupported action for auto-execution: {action_type}")

    async def _create_payment_link(self, payment: Payment, customer: Customer) -> dict[str, Any]:
        """Generate a Razorpay Payment Link for recovery."""
        if settings.demo_mode:
            if payment.amount == 999999:
                logger.error("Demo mode: Simulating execution failure (timeout).")
                raise ActionExecutionError("Simulated execution failure: upstream API timeout")
                
            logger.info("Demo mode: Simulating payment link creation.")
            return {
                "status": "success",
                "result": f"https://rzp.io/i/simulated_{uuid.uuid4().hex[:8]}",
                "provider_id": f"plink_sim_{uuid.uuid4().hex[:8]}",
                "is_simulated": True
            }

        try:
            description = f"Recovery Payment for Order {payment.order_id or payment.razorpay_payment_id}"
            response = await razorpay_client.create_payment_link(
                amount=payment.amount,
                currency=payment.currency,
                description=description,
                customer_name=customer.name,
                customer_email=customer.email,
                customer_phone=customer.phone,
                reference_id=str(payment.id)
            )
            return {
                "status": "success",
                "result": response.get("short_url", ""),
                "provider_id": response.get("id"),
                "is_simulated": False
            }
        except RazorpayClientError as e:
            logger.error(f"Failed to create payment link: {e}")
            raise ActionExecutionError(f"Payment Link API failed: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout creating payment link: {e}")
            raise ActionExecutionError(f"Payment Link API timeout: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating payment link: {e}")
            raise ActionExecutionError(f"Unexpected execution error: {e}")

action_executor = ActionExecutor()
