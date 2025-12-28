"""
Payment links routes for the cryptocurrency payment system API.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.models.payment import (
    BlockchainChain,
    CryptoCurrency,
    PaymentLinkCreate,
    PaymentLinkResponse,
    PaymentStatus,
)
from src.services.blockchain import blockchain_service
from src.services.qr_generator import qr_service
from src.services.exchange import exchange_service

router = APIRouter(prefix="/links", tags=["payment links"])

# In-memory storage for payment links (use database in production)
payment_links = {}


@router.post("", response_model=PaymentLinkResponse)
async def create_payment_link(link_data: PaymentLinkCreate):
    """
    Create a new payment link.
    
    Generates a shareable URL that customers can use to pay.
    """
    try:
        # Generate unique link ID
        link_id = uuid4().hex[:12]
        
        # Build base URL
        base_url = "http://localhost:8000"  # Configure in production
        payment_url = f"{base_url}/p/{link_id}"
        short_url = f"{base_url}/p/{link_id}"

        # Get wallet address
        merchant_wallet = link_data.merchant_wallet or \
            blockchain_service.get_wallet_for_chain(link_data.chain.value)

        # Calculate amount if fixed
        amount_crypto = None
        if link_data.amount:
            amount_crypto = await exchange_service.convert_fiat_to_crypto(
                fiat_amount=link_data.amount,
                fiat_currency=link_data.currency,
                crypto_currency=link_data.crypto_currency.value
            )

        # Set expiration
        expires_at = link_data.expires_at or datetime.utcnow() + timedelta(days=365)

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=merchant_wallet,
            amount=amount_crypto or 0,
            crypto_currency=link_data.crypto_currency.value,
            chain=link_data.chain.value,
            label="Payment Link"
        )

        # Store link data
        payment_links[link_id] = {
            "link_id": link_id,
            "payment_url": payment_url,
            "amount": link_data.amount,
            "currency": link_data.currency,
            "crypto_currency": link_data.crypto_currency.value,
            "chain": link_data.chain.value,
            "description": link_data.description,
            "wallet_address": merchant_wallet,
            "uses": 0,
            "max_uses": link_data.max_uses,
            "webhook_url": link_data.webhook_url,
            "redirect_url": link_data.redirect_url,
            "metadata": link_data.metadata,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at
        }

        return PaymentLinkResponse(
            link_id=link_id,
            payment_url=payment_url,
            short_url=short_url,
            qr_code_data_url=qr_data_url,
            amount=link_data.amount,
            currency=link_data.currency,
            crypto_currency=link_data.crypto_currency,
            chain=link_data.chain,
            description=link_data.description,
            wallet_address=merchant_wallet,
            uses=0,
            max_uses=link_data.max_uses,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment link: {str(e)}")


@router.get("/{link_id}", response_model=PaymentLinkResponse)
async def get_payment_link(link_id: str):
    """Get payment link details."""
    try:
        link_data = payment_links.get(link_id)
        if not link_data:
            raise HTTPException(status_code=404, detail="Payment link not found")

        # Check if expired
        if datetime.utcnow() > link_data["expires_at"]:
            raise HTTPException(status_code=410, detail="Payment link has expired")

        # Check usage limit
        if link_data["max_uses"] and link_data["uses"] >= link_data["max_uses"]:
            raise HTTPException(status_code=410, detail="Payment link has reached maximum uses")

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=link_data["wallet_address"],
            amount=link_data.get("amount") or 0,
            crypto_currency=link_data["crypto_currency"],
            chain=link_data["chain"]
        )

        return PaymentLinkResponse(
            link_id=link_id,
            payment_url=link_data["payment_url"],
            short_url=link_data["payment_url"],
            qr_code_data_url=qr_data_url,
            amount=link_data.get("amount"),
            currency=link_data["currency"],
            crypto_currency=CryptoCurrency(link_data["crypto_currency"]),
            chain=BlockchainChain(link_data["chain"]),
            description=link_data.get("description"),
            wallet_address=link_data["wallet_address"],
            uses=link_data["uses"],
            max_uses=link_data["max_uses"],
            created_at=link_data["created_at"],
            expires_at=link_data["expires_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment link: {str(e)}")


@router.get("/{link_id}/html", response_class=HTMLResponse)
async def get_payment_link_page(link_id: str, request: Request):
    """Get payment link page as HTML."""
    try:
        link_data = payment_links.get(link_id)
        if not link_data:
            raise HTTPException(status_code=404, detail="Payment link not found")

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=link_data["wallet_address"],
            amount=link_data.get("amount") or 0,
            crypto_currency=link_data["crypto_currency"],
            chain=link_data["chain"],
            label=link_data.get("description", "Payment")
        )

        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="src/templates")
        
        return templates.TemplateResponse(
            "link.html",
            {
                "request": request,
                "link_id": link_id,
                "link": link_data,
                "qr_code": qr_data_url,
                "amount_crypto": link_data.get("amount"),
                "currency": link_data["currency"],
                "crypto_currency": link_data["crypto_currency"].upper(),
                "chain": link_data["chain"].upper(),
                "description": link_data.get("description"),
                "wallet_address": link_data["wallet_address"],
                "payment_url": link_data["payment_url"],
                "expires_at": link_data["expires_at"].strftime("%Y-%m-%d %H:%M:%S UTC"),
                "uses": link_data["uses"],
                "max_uses": link_data["max_uses"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render payment link: {str(e)}")


@router.get("/{link_id}/stats")
async def get_link_stats(link_id: str):
    """Get payment link statistics."""
    try:
        link_data = payment_links.get(link_id)
        if not link_data:
            raise HTTPException(status_code=404, detail="Payment link not found")

        return {
            "link_id": link_id,
            "uses": link_data["uses"],
            "max_uses": link_data["max_uses"],
            "remaining_uses": link_data["max_uses"] - link_data["uses"] if link_data["max_uses"] else None,
            "created_at": link_data["created_at"],
            "expires_at": link_data["expires_at"],
            "status": "active" if datetime.utcnow() < link_data["expires_at"] else "expired"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get link stats: {str(e)}")


@router.delete("/{link_id}")
async def deactivate_payment_link(link_id: str):
    """Deactivate a payment link."""
    try:
        if link_id not in payment_links:
            raise HTTPException(status_code=404, detail="Payment link not found")

        # Remove the link
        del payment_links[link_id]

        return {
            "message": "Payment link deactivated",
            "link_id": link_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate link: {str(e)}")
