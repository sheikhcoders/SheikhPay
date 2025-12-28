"""
Blockchain service for multi-chain cryptocurrency payments.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
import httpx
from pydantic import BaseModel


class Invoice(BaseModel):
    """Model representing a payment invoice."""
    payment_id: str
    wallet_address: str
    amount_crypto: float
    crypto_currency: str
    chain: str
    amount_fiat: float
    currency: str
    status: str
    transaction_hash: Optional[str] = None
    confirmations: int = 0
    created_at: datetime
    expires_at: datetime
    webhook_url: Optional[str] = None
    metadata: Optional[dict] = None


class BlockchainService:
    """Service for monitoring blockchain transactions across multiple chains."""
    
    # Multi-chain configuration
    CHAINS = {
        "ethereum": {
            "name": "Ethereum",
            "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/demo",
            "explorer": "https://etherscan.io/tx/",
            "native_currency": "ETH",
            "chain_id": 1
        },
        "bsc": {
            "name": "BNB Smart Chain",
            "rpc_url": "https://bsc-dataseed1.binance.org",
            "explorer": "https://bscscan.com/tx/",
            "native_currency": "BNB",
            "chain_id": 56
        },
        "polygon": {
            "name": "Polygon",
            "rpc_url": "https://polygon-rpc.com",
            "explorer": "https://polygonscan.com/tx/",
            "native_currency": "MATIC",
            "chain_id": 137
        },
        "arbitrum": {
            "name": "Arbitrum",
            "rpc_url": "https://arb1.arbitrum.io/rpc",
            "explorer": "https://arbiscan.io/tx/",
            "native_currency": "ETH",
            "chain_id": 42161
        },
        "optimism": {
            "name": "Optimism",
            "rpc_url": "https://mainnet.optimism.io",
            "explorer": "https://optimistic.etherscan.io/tx/",
            "native_currency": "ETH",
            "chain_id": 10
        }
    }

    # Supported tokens per chain
    TOKENS = {
        "ethereum": ["ETH", "USDT", "USDC", "DAI"],
        "bsc": ["BNB", "USDT", "USDC", "BUSD"],
        "polygon": ["MATIC", "USDT", "USDC"],
        "arbitrum": ["ETH", "USDT", "USDC"],
        "optimism": ["ETH", "USDT", "USDC"]
    }

    # In-memory storage for invoices (use database in production)
    invoices: Dict[str, Invoice] = {}

    def __init__(
        self,
        primary_wallet: str,
        alternative_wallet: str = None,
        default_chain: str = "ethereum",
        network: str = "SANDBOX"
    ):
        """Initialize the blockchain service."""
        self.primary_wallet = primary_wallet.lower()
        self.alternative_wallet = alternative_wallet.lower() if alternative_wallet else None
        self.default_chain = default_chain
        self.network = network
        self._monitoring_task: Optional[asyncio.Task] = None

    def get_wallet_for_chain(self, chain: str) -> str:
        """Get the appropriate wallet address for a chain."""
        # Use alternative wallet for BSC, primary for others
        if chain == "bsc" and self.alternative_wallet:
            return self.alternative_wallet
        return self.primary_wallet

    def get_chain_info(self, chain: str) -> dict:
        """Get chain information."""
        return self.CHAINS.get(chain, self.CHAINS["ethereum"])

    async def start_monitoring(self):
        """Start the background blockchain monitoring task."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop the background blockchain monitoring task."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

    async def _monitor_loop(self):
        """Background loop to monitor blockchain for payments."""
        while True:
            try:
                for invoice_id, invoice in list(self.invoices.items()):
                    if invoice.status in ["pending", "waiting_for_payment"]:
                        if datetime.utcnow() > invoice.expires_at:
                            invoice.status = "expired"
                        else:
                            await self._check_payment(invoice)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            await asyncio.sleep(30)  # Check every 30 seconds

    async def _check_payment(self, invoice: Invoice):
        """Check if a payment has been received for an invoice."""
        if self.network == "SANDBOX":
            # Simulate payment detection in sandbox mode
            await self._simulate_payment_detection(invoice)
        else:
            # Production blockchain monitoring
            # This would query RPC nodes or use services like Infura/Alchemy
            pass

    async def _simulate_payment_detection(self, invoice: Invoice):
        """Simulate payment detection for sandbox testing."""
        # In sandbox, we simulate successful payment
        invoice.status = "payment_received"
        invoice.transaction_hash = f"0x{invoice.payment_id.replace('-', '')[:64]}"
        invoice.confirmations = 1

        # Trigger webhook if configured
        if invoice.webhook_url:
            await self._send_webhook(invoice)

    async def _send_webhook(self, invoice: Invoice):
        """Send payment notification webhook."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "event": "payment.completed",
                    "payment_id": invoice.payment_id,
                    "amount": invoice.amount_crypto,
                    "currency": invoice.crypto_currency,
                    "chain": invoice.chain,
                    "wallet_address": invoice.wallet_address,
                    "transaction_hash": invoice.transaction_hash,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await client.post(
                    invoice.webhook_url,
                    json=payload,
                    timeout=10.0
                )
        except Exception as e:
            print(f"Failed to send webhook: {e}")

    async def create_payment(
        self,
        payment_id: str,
        amount_crypto: float,
        crypto_currency: str,
        chain: str,
        amount_fiat: float,
        currency: str,
        expires_at: datetime,
        webhook_url: Optional[str] = None,
        metadata: Optional[dict] = None,
        merchant_wallet: Optional[str] = None
    ) -> Invoice:
        """Create a new payment invoice."""
        # Get wallet for this chain
        wallet_address = merchant_wallet or self.get_wallet_for_chain(chain)
        
        invoice = Invoice(
            payment_id=payment_id,
            wallet_address=wallet_address,
            amount_crypto=amount_crypto,
            crypto_currency=crypto_currency,
            chain=chain,
            amount_fiat=amount_fiat,
            currency=currency,
            status="waiting_for_payment",
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            webhook_url=webhook_url,
            metadata=metadata
        )
        self.invoices[payment_id] = invoice
        return invoice

    def get_payment(self, payment_id: str) -> Optional[Invoice]:
        """Get a payment by ID."""
        return self.invoices.get(payment_id)

    def get_chain_explorer_url(self, chain: str, tx_hash: str) -> str:
        """Get blockchain explorer URL for a transaction."""
        base_url = self.CHAINS.get(chain, self.CHAINS["ethereum"])["explorer"]
        return f"{base_url}{tx_hash}"


# Create singleton instance with wallets from environment
blockchain_service = BlockchainService(
    primary_wallet="0x9646b67E78e81F88eb59177ec5a8c38fD2B0dcA2",
    alternative_wallet="0xb549579a6d5ccfa3f8b143d11bcb4bf1494f7880",
    default_chain="ethereum",
    network="SANDBOX"
)
