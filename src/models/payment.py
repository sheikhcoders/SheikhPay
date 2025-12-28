"""
Payment models for the cryptocurrency payment system.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, Field


class BlockchainChain(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


class PaymentStatus(str, Enum):
    """Payment status states."""
    PENDING = "pending"
    WAITING_FOR_PAYMENT = "waiting_for_payment"
    PAYMENT_RECEIVED = "payment_received"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"
    REFUNDED = "refunded"


class CryptoCurrency(str, Enum):
    """Supported cryptocurrencies."""
    ETH = "ETH"
    USDT = "USDT"
    USDC = "USDC"
    BNB = "BNB"
    MATIC = "MATIC"
    DAI = "DAI"


# ==================== Payment Models ====================

class PaymentCreate(BaseModel):
    """Request model for creating a payment."""
    amount: float = Field(..., gt=0, description="Amount in fiat currency")
    currency: str = Field(default="USD", description="Fiat currency code")
    crypto_currency: CryptoCurrency = Field(default=CryptoCurrency.ETH, description="Cryptocurrency to receive")
    chain: BlockchainChain = Field(default=BlockchainChain.ETHEREUM, description="Blockchain network")
    description: Optional[str] = Field(None, description="Payment description")
    merchant_wallet: Optional[str] = Field(None, description="Specific wallet to receive payment")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    redirect_url: Optional[str] = Field(None, description="URL to redirect after payment")
    customer_email: Optional[str] = Field(None, description="Customer email for notifications")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class PaymentResponse(BaseModel):
    """Response model for payment details."""
    payment_id: str
    status: PaymentStatus
    amount_fiat: float
    currency: str
    amount_crypto: float
    crypto_currency: CryptoCurrency
    chain: BlockchainChain
    wallet_address: str
    qr_code_data_url: str
    payment_uri: str
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    created_at: datetime
    expires_at: datetime
    metadata: Optional[dict] = None


class PaymentStatusResponse(BaseModel):
    """Response model for payment status check."""
    payment_id: str
    status: PaymentStatus
    amount_crypto: float
    crypto_currency: CryptoCurrency
    chain: BlockchainChain
    wallet_address: str
    transaction_hash: Optional[str] = None
    confirmations: int
    created_at: datetime
    expires_at: datetime
    updated_at: datetime


# ==================== Invoice Models ====================

class InvoiceItem(BaseModel):
    """Invoice line item."""
    description: str
    quantity: int = 1
    amount: float


class InvoiceCreate(BaseModel):
    """Request model for creating an invoice."""
    customer_email: str
    customer_name: Optional[str] = None
    items: List[InvoiceItem]
    currency: str = Field(default="USD", description="Fiat currency")
    chain: BlockchainChain = Field(default=BlockchainChain.ETHEREUM, description="Blockchain network")
    crypto_currency: CryptoCurrency = Field(default=CryptoCurrency.ETH, description="Cryptocurrency")
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    merchant_wallet: Optional[str] = None
    webhook_url: Optional[str] = None
    redirect_url: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Response model for invoice details."""
    invoice_id: str
    invoice_number: str
    status: PaymentStatus
    customer_email: str
    customer_name: Optional[str]
    items: List[InvoiceItem]
    subtotal: float
    tax: float = 0
    total: float
    currency: str
    amount_crypto: float
    crypto_currency: CryptoCurrency
    chain: BlockchainChain
    wallet_address: str
    qr_code_data_url: str
    invoice_url: str
    payment_url: str
    due_date: Optional[datetime]
    created_at: datetime
    expires_at: datetime


# ==================== Payment Link Models ====================

class PaymentLinkCreate(BaseModel):
    """Request model for creating a payment link."""
    amount: Optional[float] = Field(None, gt=0, description="Fixed amount (optional)")
    currency: str = Field(default="USD", description="Fiat currency")
    crypto_currency: CryptoCurrency = Field(default=CryptoCurrency.ETH, description="Cryptocurrency")
    chain: BlockchainChain = Field(default=BlockchainChain.ETHEREUM, description="Blockchain network")
    description: Optional[str] = Field(None, description="Payment description")
    merchant_wallet: Optional[str] = None
    webhook_url: Optional[str] = None
    redirect_url: Optional[str] = None
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum uses")
    expires_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class PaymentLinkResponse(BaseModel):
    """Response model for payment link."""
    link_id: str
    payment_url: str
    short_url: str
    qr_code_data_url: str
    amount: Optional[float]
    currency: str
    crypto_currency: CryptoCurrency
    chain: BlockchainChain
    description: Optional[str]
    wallet_address: str
    uses: int = 0
    max_uses: Optional[int]
    created_at: datetime
    expires_at: Optional[datetime]


# ==================== Merchant Models ====================

class MerchantConfig(BaseModel):
    """Merchant configuration."""
    wallet_address: str
    chain: BlockchainChain = BlockchainChain.ETHEREUM
    webhook_secret: str
    notification_email: Optional[str] = None
    default_currency: str = "USD"


class TransactionHistoryItem(BaseModel):
    """Transaction history item."""
    id: str
    type: str  # payment, invoice, refund
    amount: float
    currency: str
    crypto_amount: float
    crypto_currency: str
    status: PaymentStatus
    created_at: datetime
    transaction_hash: Optional[str] = None


# ==================== Webhook Models ====================

class WebhookPayload(BaseModel):
    """Webhook payload."""
    event: str
    payment_id: Optional[str] = None
    invoice_id: Optional[str] = None
    link_id: Optional[str] = None
    amount: float
    currency: str
    crypto_amount: float
    crypto_currency: str
    chain: BlockchainChain
    wallet_address: str
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    timestamp: datetime
    metadata: Optional[dict] = None


class WebhookResponse(BaseModel):
    """Webhook response."""
    received: bool
    event: str
    payment_id: Optional[str] = None
