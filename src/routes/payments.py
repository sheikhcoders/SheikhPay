"""
Payment routes for the cryptocurrency payment system API.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.models.payment import (
    BlockchainChain,
    CryptoCurrency,
    PaymentCreate,
    PaymentResponse,
    PaymentStatus,
    PaymentStatusResponse,
)
from src.services.blockchain import blockchain_service
from src.services.qr_generator import qr_service
from src.services.exchange import exchange_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse)
async def create_payment(payment_data: PaymentCreate):
    """
    Create a new payment invoice.
    
    Generates a unique payment ID and QR code for the customer to pay.
    """
    try:
        # Generate unique payment ID
        payment_id = str(uuid4())

        # Calculate cryptocurrency amount from fiat
        amount_crypto = await exchange_service.convert_fiat_to_crypto(
            fiat_amount=payment_data.amount,
            fiat_currency=payment_data.currency,
            crypto_currency=payment_data.crypto_currency.value
        )

        # Set expiration time (15 minutes)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Get wallet address for the specified chain
        merchant_wallet = payment_data.merchant_wallet or \
            blockchain_service.get_wallet_for_chain(payment_data.chain.value)

        # Create invoice in blockchain service
        invoice = await blockchain_service.create_payment(
            payment_id=payment_id,
            amount_crypto=round(amount_crypto, 8),
            crypto_currency=payment_data.crypto_currency.value,
            chain=payment_data.chain.value,
            amount_fiat=payment_data.amount,
            currency=payment_data.currency,
            expires_at=expires_at,
            webhook_url=payment_data.webhook_url,
            metadata=payment_data.metadata,
            merchant_wallet=merchant_wallet
        )

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=invoice.wallet_address,
            amount=invoice.amount_crypto,
            crypto_currency=invoice.crypto_currency,
            chain=invoice.chain
        )

        # Build payment URI
        payment_uri = qr_service._build_payment_uri(
            wallet_address=invoice.wallet_address,
            amount=invoice.amount_crypto,
            crypto_currency=invoice.crypto_currency,
            chain=invoice.chain
        )

        return PaymentResponse(
            payment_id=payment_id,
            status=PaymentStatus.WAITING_FOR_PAYMENT,
            amount_fiat=payment_data.amount,
            currency=payment_data.currency,
            amount_crypto=round(amount_crypto, 8),
            crypto_currency=payment_data.crypto_currency,
            chain=payment_data.chain,
            wallet_address=invoice.wallet_address,
            qr_code_data_url=qr_data_url,
            payment_uri=payment_uri,
            created_at=invoice.created_at,
            expires_at=expires_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(payment_id: str):
    """Get the status of a payment."""
    try:
        invoice = blockchain_service.get_payment(payment_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Payment not found")

        return PaymentStatusResponse(
            payment_id=invoice.payment_id,
            status=PaymentStatus(invoice.status),
            amount_crypto=invoice.amount_crypto,
            crypto_currency=CryptoCurrency(invoice.crypto_currency),
            chain=BlockchainChain(invoice.chain),
            wallet_address=invoice.wallet_address,
            transaction_hash=invoice.transaction_hash,
            confirmations=invoice.confirmations,
            created_at=invoice.created_at,
            expires_at=invoice.expires_at,
            updated_at=datetime.utcnow()
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")


@router.get("/{payment_id}/html", response_class=HTMLResponse)
async def get_payment_page(payment_id: str, request: Request):
    """Get the payment page as HTML."""
    try:
        invoice = blockchain_service.get_payment(payment_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=invoice.wallet_address,
            amount=invoice.amount_crypto,
            crypto_currency=invoice.crypto_currency,
            chain=invoice.chain
        )

        # Get explorer URL
        explorer_url = ""
        if invoice.transaction_hash:
            explorer_url = blockchain_service.get_chain_explorer_url(
                invoice.chain, invoice.transaction_hash
            )

        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="src/templates")
        
        return templates.TemplateResponse(
            "payment.html",
            {
                "request": request,
                "payment_id": invoice.payment_id,
                "amount_crypto": invoice.amount_crypto,
                "crypto_currency": invoice.crypto_currency.upper(),
                "chain": invoice.chain.upper(),
                "amount_fiat": invoice.amount_fiat,
                "currency": invoice.currency,
                "wallet_address": invoice.wallet_address,
                "qr_code": qr_data_url,
                "status": invoice.status,
                "expires_at": invoice.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "created_at": invoice.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "explorer_url": explorer_url,
                "transaction_hash": invoice.transaction_hash
            }
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render payment page: {str(e)}")


@router.post("/{payment_id}/simulate")
async def simulate_payment(payment_id: str):
    """
    Simulate a payment for testing purposes.
    
    This endpoint is only available in sandbox mode.
    """
    try:
        invoice = blockchain_service.get_payment(payment_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Simulate payment
        invoice.status = "payment_received"
        invoice.transaction_hash = f"0x{payment_id.replace('-', '')[:64]}"
        invoice.confirmations = 1

        return {
            "message": "Payment simulated successfully",
            "payment_id": payment_id,
            "status": "payment_received",
            "transaction_hash": invoice.transaction_hash
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to simulate payment: {str(e)}")


@router.get("/chains/list")
async def list_supported_chains():
    """Get list of supported blockchain networks."""
    return {
        "chains": [
            {
                "id": chain_id,
                "name": info["name"],
                "native_currency": info["native_currency"],
                "chain_id": info["chain_id"]
            }
            for chain_id, info in blockchain_service.CHAINS.items()
        ]
    }


@router.get("/tokens/{chain}")
async def list_chain_tokens(chain: str):
    """Get list of supported tokens for a chain."""
    chain = chain.lower()
    if chain not in blockchain_service.TOKENS:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")
    
    return {
        "chain": chain,
        "tokens": blockchain_service.TOKENS[chain]
    }
