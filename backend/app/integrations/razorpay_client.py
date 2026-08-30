"""Razorpay API client — isolated integration layer.

Uses httpx for async HTTP calls to the official Razorpay API.
All endpoints referenced here are from official Razorpay documentation:
  - GET  https://api.razorpay.com/v1/payments/{id}
  - POST https://api.razorpay.com/v1/payment_links/

Authentication: Basic Auth with key_id:key_secret.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"
DEFAULT_TIMEOUT = 15.0  # seconds


class RazorpayClientError(Exception):
    """Raised when a Razorpay API call fails."""

    def __init__(self, status_code: int | None, message: str, response_body: Any = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class RazorpayClient:
    """Async client for the Razorpay REST API (Test Mode compatible).

    All methods return parsed JSON dicts. On error they raise
    RazorpayClientError with the HTTP status code and error details.
    """

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
        base_url: str = RAZORPAY_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.key_id = key_id or settings.razorpay_key_id
        self.key_secret = key_secret or settings.razorpay_key_secret
        self.base_url = base_url
        self.timeout = timeout

        if not self.key_id or not self.key_secret:
            logger.warning(
                "Razorpay credentials not configured. "
                "API calls will fail until RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set."
            )

    def _auth(self) -> tuple[str, str]:
        """Return Basic Auth tuple."""
        return (self.key_id, self.key_secret)

    async def _request(
        self,
        method: str,
        path: str,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an authenticated request to the Razorpay API.

        Handles timeouts, HTTP errors, and returns the parsed JSON response.
        """
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    auth=self._auth(),
                    json=json_body,
                    params=params,
                )
        except httpx.TimeoutException:
            raise RazorpayClientError(
                status_code=None,
                message=f"Razorpay API request timed out: {method} {path}",
            )
        except httpx.RequestError as e:
            raise RazorpayClientError(
                status_code=None,
                message=f"Razorpay API request failed: {e}",
            )

        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text

            error_msg = error_body
            if isinstance(error_body, dict) and "error" in error_body:
                error_msg = error_body["error"].get("description", str(error_body))

            raise RazorpayClientError(
                status_code=response.status_code,
                message=f"Razorpay API error ({response.status_code}): {error_msg}",
                response_body=error_body,
            )

        return response.json()

    # ----- Payment APIs (official: https://razorpay.com/docs/api/payments) -----

    async def fetch_payment(self, payment_id: str) -> dict:
        """Fetch a payment by its Razorpay payment ID.

        Official endpoint: GET /v1/payments/{payment_id}
        Docs: https://razorpay.com/docs/api/payments#fetch-a-payment

        Returns the full payment entity dict.
        """
        return await self._request("GET", f"/payments/{payment_id}")

    async def fetch_all_payments(
        self,
        count: int = 10,
        skip: int = 0,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
    ) -> dict:
        """Fetch multiple payments with pagination.

        Official endpoint: GET /v1/payments
        Docs: https://razorpay.com/docs/api/payments#fetch-all-payments
        """
        params: dict[str, Any] = {"count": count, "skip": skip}
        if from_timestamp:
            params["from"] = from_timestamp
        if to_timestamp:
            params["to"] = to_timestamp
        return await self._request("GET", "/payments", params=params)

    # ----- Payment Link APIs (official: https://razorpay.com/docs/api/payment-links) -----

    async def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        description: str = "",
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        reference_id: str | None = None,
        expire_by: int | None = None,
        callback_url: str | None = None,
    ) -> dict:
        """Create a payment link for recovery.

        Official endpoint: POST /v1/payment_links/
        Docs: https://razorpay.com/docs/api/payment-links#create-payment-link

        Args:
            amount: Amount in smallest currency unit (paise for INR).
            currency: ISO currency code. Default "INR".
            description: Description shown on the payment link page.
            customer_name: Customer name (optional).
            customer_email: Customer email (optional).
            customer_phone: Customer phone with country code (optional).
            reference_id: Your internal reference ID (optional).
            expire_by: Unix timestamp for link expiry (optional).
            callback_url: Redirect URL after payment (optional).

        Returns the payment link entity dict including 'short_url'.
        """
        body: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "description": description,
        }

        # Build customer object only if we have details
        customer: dict[str, str] = {}
        if customer_name:
            customer["name"] = customer_name
        if customer_email:
            customer["email"] = customer_email
        if customer_phone:
            customer["contact"] = customer_phone
        if customer:
            body["customer"] = customer

        if reference_id:
            body["reference_id"] = reference_id
        if expire_by:
            body["expire_by"] = expire_by
        if callback_url:
            body["callback_url"] = callback_url
            body["callback_method"] = "get"

        # Enable SMS/email notifications
        body["notify"] = {"sms": bool(customer_phone), "email": bool(customer_email)}

        return await self._request("POST", "/payment_links/", json_body=body)

    async def fetch_payment_link(self, link_id: str) -> dict:
        """Fetch a payment link by ID.

        Official endpoint: GET /v1/payment_links/{link_id}
        """
        return await self._request("GET", f"/payment_links/{link_id}")


# Module-level singleton for convenience
razorpay_client = RazorpayClient()
