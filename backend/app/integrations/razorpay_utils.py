"""Razorpay utilities for webhook validation."""

import hmac
import hashlib
from app.config import settings

class SignatureVerificationError(Exception):
    """Raised when webhook signature verification fails."""
    pass

def verify_webhook_signature(payload_body: bytes, signature: str, secret: str | None = None) -> bool:
    """Verifies the Razorpay webhook signature using HMAC SHA256.

    Args:
        payload_body: The RAW bytes of the request body. Must not be parsed JSON.
        signature: The signature passed in the X-Razorpay-Signature header.
        secret: The webhook secret. Defaults to settings.razorpay_webhook_secret.

    Raises:
        SignatureVerificationError: If the signature is invalid.
        
    Returns:
        True if valid.
    """
    secret = secret or settings.razorpay_webhook_secret
    if not secret:
        raise SignatureVerificationError("Webhook secret not configured.")
        
    if not signature:
        raise SignatureVerificationError("No signature provided.")

    secret_bytes = secret.encode("utf-8")
    
    # Compute HMAC SHA256
    computed_signature = hmac.new(
        key=secret_bytes,
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # compare_digest prevents timing attacks
    if not hmac.compare_digest(computed_signature, signature):
        raise SignatureVerificationError("Invalid signature.")
        
    return True
