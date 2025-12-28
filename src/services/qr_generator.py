"""
QR Code generation service for cryptocurrency payments.
"""
import base64
import io
from typing import Optional
import qrcode
from PIL import Image


class QRCodeService:
    """Service for generating QR codes for cryptocurrency payments."""

    def __init__(self):
        """Initialize the QR code service."""
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

    def generate_payment_qr(
        self,
        wallet_address: str,
        amount: float,
        crypto_currency: str,
        chain: str = "ethereum",
        label: Optional[str] = None
    ) -> str:
        """
        Generate a QR code for a cryptocurrency payment.

        Args:
            wallet_address: The cryptocurrency wallet address
            amount: Amount of cryptocurrency to request
            crypto_currency: The cryptocurrency symbol
            chain: The blockchain network
            label: Optional label for the payment

        Returns:
            Base64-encoded data URL of the QR code image
        """
        # Build the payment URI
        payment_uri = self._build_payment_uri(
            wallet_address=wallet_address,
            amount=amount,
            crypto_currency=crypto_currency,
            chain=chain,
            label=label
        )

        # Generate QR code
        self.qr.clear()
        self.qr.add_data(payment_uri)
        self.qr.make(fit=True)

        # Create image
        img = self.qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 data URL
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{qr_base64}"

    def _build_payment_uri(
        self,
        wallet_address: str,
        amount: float,
        crypto_currency: str,
        chain: str,
        label: Optional[str] = None
    ) -> str:
        """
        Build a cryptocurrency payment URI.

        Supports multiple blockchain URI formats:
        - Ethereum: EIP-681
        - Bitcoin: BIP-21
        - Generic format for other chains
        """
        crypto_currency = crypto_currency.upper()
        chain = chain.lower()

        if crypto_currency == "ETH" or chain == "ethereum":
            # Ethereum payment URI (EIP-681)
            uri = f"ethereum:{wallet_address}"
            if amount > 0:
                uri += f"?value={int(amount * 10**18)}"
            if label:
                uri += f"&label={label}"
            return uri

        elif crypto_currency == "BNB" or chain == "bsc":
            # BSC uses same format as Ethereum
            uri = f"ethereum:{wallet_address}"
            if amount > 0:
                uri += f"?value={int(amount * 10**18)}"
            return uri

        elif crypto_currency == "MATIC" or chain == "polygon":
            # Polygon uses same format as Ethereum
            uri = f"ethereum:{wallet_address}"
            if amount > 0:
                uri += f"?value={int(amount * 10**18)}"
            return uri

        elif crypto_currency == "BTC":
            # Bitcoin payment URI (BIP-21)
            uri = f"bitcoin:{wallet_address}"
            params = []
            if amount > 0:
                params.append(f"amount={amount}")
            if label:
                params.append(f"label={label}")
            if params:
                uri += "?" + "&".join(params)
            return uri

        else:
            # Generic URI format for other tokens/chains
            uri = f"{crypto_currency.lower()}:{wallet_address}"
            params = []
            if amount > 0:
                params.append(f"amount={amount}")
            if chain:
                params.append(f"chain={chain}")
            if params:
                uri += "?" + "&".join(params)
            return uri

    def generate_address_qr(self, wallet_address: str) -> str:
        """
        Generate a simple QR code for a wallet address.

        Args:
            wallet_address: The cryptocurrency wallet address

        Returns:
            Base64-encoded data URL of the QR code image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(wallet_address)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{qr_base64}"


# Singleton instance
qr_service = QRCodeService()
