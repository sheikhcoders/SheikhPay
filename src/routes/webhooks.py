"""
Webhook routes for payment notifications.
"""
import hmac
import hashlib
import json
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from src.models.payment import WebhookPayload, WebhookResponse
from src.services.blockchain import blockchain_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Store received webhooks for verification
webhook_logs = []


@router.post("/callback", response_model=WebhookResponse)
async def receive_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Receive payment webhook notifications.
    
    This endpoint is called by the payment system when a payment is confirmed.
    """
    try:
        # Log the webhook
        webhook_logs.append({
            "event": payload.event,
            "payment_id": payload.payment_id,
            "timestamp": payload.timestamp
        })

        # Handle different event types
        if payload.event == "payment.completed":
            # Update payment status
            if payload.payment_id:
                invoice = blockchain_service.get_payment(payload.payment_id)
                if invoice:
                    invoice.status = "confirmed"
                    invoice.transaction_hash = payload.transaction_hash
                    invoice.confirmations = payload.confirmations

        elif payload.event == "payment.failed":
            # Handle failed payment
            if payload.payment_id:
                invoice = blockchain_service.get_payment(payload.payment_id)
                if invoice:
                    invoice.status = "failed"

        # Process webhook in background (send to merchant's system)
        background_tasks.add_task(
            process_webhook,
            payload
        )

        return WebhookResponse(
            received=True,
            event=payload.event,
            payment_id=payload.payment_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/verify")
async def verify_webhook(request: Request):
    """
    Verify a webhook signature.
    
    Merchants can use this to verify that webhooks are from the payment system.
    """
    try:
        body = await request.body()
        signature = request.headers.get("X-Webhook-Signature")
        webhook_secret = request.headers.get("X-Webhook-Secret")

        if not signature or not webhook_secret:
            raise HTTPException(status_code=400, detail="Missing signature or secret")

        # Verify signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        return {"valid": True, "message": "Webhook signature verified"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.get("/logs")
async def get_webhook_logs(limit: int = 100):
    """Get recent webhook logs (for debugging)."""
    return {
        "logs": webhook_logs[-limit:],
        "total": len(webhook_logs)
    }


async def process_webhook(payload: WebhookPayload):
    """
    Process webhook payload.
    
    This is called in the background to avoid blocking the response.
    In production, this would send data to the merchant's system.
    """
    # In production, send to merchant's webhook URL
    # For now, just log
    print(f"Processing webhook: {payload.event} for payment {payload.payment_id}")


def create_webhook_payload(
    event: str,
    payment_id: str,
    amount: float,
    currency: str,
    crypto_amount: float,
    crypto_currency: str,
    chain: str,
    wallet_address: str,
    transaction_hash: str = None,
    metadata: dict = None
) -> WebhookPayload:
    """Create a webhook payload for sending to merchants."""
    from datetime import datetime
    
    return WebhookPayload(
        event=event,
        payment_id=payment_id,
        amount=amount,
        currency=currency,
        crypto_amount=crypto_amount,
        crypto_currency=crypto_currency,
        chain=chain,
        wallet_address=wallet_address,
        transaction_hash=transaction_hash,
        timestamp=datetime.utcnow(),
        metadata=metadata
    )
