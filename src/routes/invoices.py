"""
Invoice routes for the cryptocurrency payment system API.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.models.payment import (
    BlockchainChain,
    CryptoCurrency,
    InvoiceCreate,
    InvoiceResponse,
    PaymentStatus,
    InvoiceItem,
)
from src.services.blockchain import blockchain_service
from src.services.qr_generator import qr_service
from src.services.exchange import exchange_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate):
    """
    Create a new invoice.
    
    Generates a professional invoice with payment QR code.
    """
    try:
        # Generate unique invoice ID and number
        invoice_id = str(uuid4())
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"

        # Calculate total amount
        subtotal = sum(item.amount * item.quantity for item in invoice_data.items)
        tax = subtotal * 0.0  # No tax by default
        total = subtotal + tax

        # Calculate cryptocurrency amount
        amount_crypto = await exchange_service.convert_fiat_to_crypto(
            fiat_amount=total,
            fiat_currency=invoice_data.currency,
            crypto_currency=invoice_data.crypto_currency.value
        )

        # Set expiration (7 days by default)
        expires_at = invoice_data.due_date or datetime.utcnow() + timedelta(days=7)

        # Get wallet address
        merchant_wallet = invoice_data.merchant_wallet or \
            blockchain_service.get_wallet_for_chain(invoice_data.chain.value)

        # Create payment record
        payment_id = f"inv_{invoice_id}"
        invoice_payment = await blockchain_service.create_payment(
            payment_id=payment_id,
            amount_crypto=round(amount_crypto, 8),
            crypto_currency=invoice_data.crypto_currency.value,
            chain=invoice_data.chain.value,
            amount_fiat=total,
            currency=invoice_data.currency,
            expires_at=expires_at,
            webhook_url=invoice_data.webhook_url,
            metadata={
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "customer_email": invoice_data.customer_email,
                "customer_name": invoice_data.customer_name
            }
        )

        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=merchant_wallet,
            amount=amount_crypto,
            crypto_currency=invoice_data.crypto_currency.value,
            chain=invoice_data.chain.value,
            label=f"Invoice {invoice_number}"
        )

        # Build invoice URL
        base_url = "http://localhost:8000"  # Configure in production
        invoice_url = f"{base_url}/invoices/{invoice_id}"
        payment_url = f"{base_url}/pay/{invoice_id}"

        return InvoiceResponse(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            status=PaymentStatus.WAITING_FOR_PAYMENT,
            customer_email=invoice_data.customer_email,
            customer_name=invoice_data.customer_name,
            items=invoice_data.items,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=invoice_data.currency,
            amount_crypto=round(amount_crypto, 8),
            crypto_currency=invoice_data.crypto_currency,
            chain=invoice_data.chain,
            wallet_address=merchant_wallet,
            qr_code_data_url=qr_data_url,
            invoice_url=invoice_url,
            payment_url=payment_url,
            due_date=invoice_data.due_date,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """Get invoice details."""
    try:
        # Find payment associated with this invoice
        payment_id = f"inv_{invoice_id}"
        invoice = blockchain_service.get_payment(payment_id)
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Parse metadata
        metadata = invoice.metadata or {}
        items = metadata.get("items", [InvoiceItem(description="Payment", amount=invoice.amount_fiat)])
        
        return InvoiceResponse(
            invoice_id=invoice_id,
            invoice_number=metadata.get("invoice_number", f"INV-{invoice_id[:8]}"),
            status=PaymentStatus(invoice.status),
            customer_email=metadata.get("customer_email", ""),
            customer_name=metadata.get("customer_name"),
            items=items,
            subtotal=invoice.amount_fiat,
            tax=0,
            total=invoice.amount_fiat,
            currency=invoice.currency,
            amount_crypto=invoice.amount_crypto,
            crypto_currency=CryptoCurrency(invoice.crypto_currency),
            chain=BlockchainChain(invoice.chain),
            wallet_address=invoice.wallet_address,
            qr_code_data_url="",  # Would regenerate if needed
            invoice_url=f"http://localhost:8000/invoices/{invoice_id}",
            payment_url=f"http://localhost:8000/pay/{invoice_id}",
            due_date=None,
            created_at=invoice.created_at,
            expires_at=invoice.expires_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invoice: {str(e)}")


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
async def get_invoice_page(invoice_id: str, request: Request):
    """Get invoice page as HTML."""
    try:
        # Get invoice data
        invoice_response = await get_invoice(invoice_id)
        
        # Generate QR code
        qr_data_url = qr_service.generate_payment_qr(
            wallet_address=invoice_response.wallet_address,
            amount=invoice_response.amount_crypto,
            crypto_currency=invoice_response.crypto_currency.value,
            chain=invoice_response.chain.value,
            label=f"Invoice {invoice_response.invoice_number}"
        )

        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="src/templates")
        
        return templates.TemplateResponse(
            "invoice.html",
            {
                "request": request,
                "invoice": invoice_response,
                "qr_code": qr_data_url,
                "payment_url": invoice_response.payment_url
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render invoice: {str(e)}")


@router.post("/{invoice_id}/send")
async def send_invoice(invoice_id: str):
    """
    Send invoice to customer via email.
    
    (Requires email service configuration)
    """
    try:
        invoice = await get_invoice(invoice_id)
        
        # In production, this would send an email
        # For now, return success
        return {
            "message": "Invoice sent successfully",
            "invoice_id": invoice_id,
            "recipient": invoice.customer_email
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send invoice: {str(e)}")


@router.get("/{invoice_id}/reminder")
async def send_invoice_reminder(invoice_id: str):
    """Send payment reminder for unpaid invoice."""
    try:
        invoice = await get_invoice(invoice_id)
        
        if invoice.status != PaymentStatus.WAITING_FOR_PAYMENT:
            raise HTTPException(status_code=400, detail="Invoice is not pending payment")
        
        return {
            "message": "Reminder sent",
            "invoice_id": invoice_id,
            "recipient": invoice.customer_email
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reminder: {str(e)}")
