# Cryptocurrency Payment System
# Non-custodial payments directly to your wallet - no frozen funds!

## 🎯 Features

### Core Features
- ✅ **Direct Wallet Payments** - No middleman, funds go directly to your wallet
- ✅ **Multiple EVM Chains** - Ethereum, BSC, Polygon, Arbitrum, etc.
- ✅ **Multi-Currency Support** - ETH, USDT, USDC, BNB, MATIC, etc.
- ✅ **Payment Links** - Generate shareable payment links
- ✅ **Invoices** - Create professional invoices
- ✅ **Webhooks** - Real-time payment notifications

### E-commerce Integrations
- ✅ **WooCommerce** - WordPress plugin
- ✅ **Shopify** - App integration
- ✅ **WHMCS** - Hosting billing system
- ✅ **Telegram Mini App** - Payment bot
- ✅ **Custom API** - Build your own integration

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn jinja2 pydantic qrcode[pil] httpx python-dotenv
```

### 2. Configure Environment
Edit `.env` file:
```env
# Primary Merchant Wallet (Ethereum/BSC/etc)
MERCHANT_WALLET=0x9646b67E78e81F88eb59177ec5a8c38fD2B0dcA2

# Alternative Merchant Wallet
ALTERNATIVE_WALLET=0xb549579a6d5ccfa3f8b143d11bcb4bf1494f7880

# Network Mode: SANDBOX or PRODUCTION
NETWORK_ENV=PRODUCTION

# Supported Chains
SUPPORTED_CHAINS=ethereum,bsc,polygon,arbitrum

# Default Chain
DEFAULT_CHAIN=ethereum
```

### 3. Run the Server
```bash
python src/main.py
```

### 4. Access the System
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Payment Link Demo**: http://localhost:8000/pay/demo

## 📁 Project Structure

```
crypto-pay-system/
├── src/
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── payments.py      # Payment endpoints
│   │   ├── invoices.py      # Invoice management
│   │   ├── links.py         # Payment links
│   │   ├── webhooks.py      # Webhook handlers
│   │   └── integrations.py  # E-commerce integrations
│   ├── services/
│   │   ├── blockchain.py    # Multi-chain support
│   │   ├── exchange.py      # Exchange rates
│   │   ├── qr_generator.py  # QR code generation
│   │   └── notifications.py # Webhook/push notifications
│   ├── models/
│   │   ├── payment.py       # Payment models
│   │   ├── invoice.py       # Invoice models
│   │   └── merchant.py      # Merchant models
│   ├── templates/
│   │   ├── payment.html     # Payment page
│   │   ├── invoice.html     # Invoice template
│   │   ├── link.html        # Payment link page
│   │   ├── dashboard.html   # Merchant dashboard
│   │   └── telegram.html    # Telegram Mini App
│   └── static/
│       ├── css/style.css    # Styles
│       └── js/payment.js    # Frontend JavaScript
├── integration-plugins/
│   ├── woocommerce/         # WordPress/WooCommerce
│   ├── shopify/             # Shopify App
│   ├── whmcs/               # WHMCS Module
│   └── telegram/            # Telegram Bot
└── docs/
    ├── API.md               # API Documentation
    ├── PLUGINS.md           # Plugin Documentation
    └── DEPLOYMENT.md        # Deployment Guide
```

## 🔗 Payment Links

Create instant payment links:

```bash
# Create payment link
POST /api/v1/links
{
    "amount": 100,
    "currency": "USD",
    "chain": "ethereum",
    "description": "Order #12345",
    "redirect_url": "https://yourstore.com/success"
}

# Response
{
    "link_id": "abc123xyz",
    "payment_url": "https://pay.example.com/p/abc123xyz",
    "qr_code": "data:image/png;base64,..."
}
```

**Share the link or show the QR code!**

## 📄 Invoice System

Create professional invoices:

```bash
# Create invoice
POST /api/v1/invoices
{
    "customer_email": "customer@example.com",
    "items": [
        {"description": "Product 1", "amount": 50},
        {"description": "Product 2", "amount": 50}
    ],
    "currency": "USD",
    "chain": "bsc"
}

# Response
{
    "invoice_id": "inv_abc123",
    "invoice_url": "https://pay.example.com/inv/abc123",
    "due_date": "2025-12-29T09:38:00Z"
}
```

## 🛒 E-commerce Integrations

### WooCommerce (WordPress)
```php
// Add to your WordPress theme's functions.php
require_once 'crypto-pay-woocommerce.php';
```

### Shopify
1. Install app from Shopify App Store
2. Configure wallet address in settings
3. Enable crypto payments at checkout

### WHMCS
```bash
# Upload to /modules/gateways/
cp crypto-pay-whmcs /var/www/html/whmcs/modules/gateways/
```

### Telegram Mini App
1. Create Telegram Bot via @BotFather
2. Configure webhook URL
3. Users can pay directly in chat

## 🔗 Supported Chains & Tokens

| Chain | Native | ERC-20 Tokens |
|-------|--------|---------------|
| Ethereum | ETH | USDT, USDC, DAI |
| BSC | BNB | USDT, USDC, BUSD |
| Polygon | MATIC | USDT, USDC |
| Arbitrum | ETH | USDT, USDC |
| Optimism | ETH | USDT, USDC |

## 💰 Multiple Merchant Wallets

```env
# Primary wallet (default)
MERCHANT_WALLET=0x9646b67E78e81F88eb59177ec5a8c38fD2B0dcA2

# Alternative wallet
ALTERNATIVE_WALLET=0xb549579a6d5ccfa3f8b143d11bcb4bf1494f7880

# Route payments to different wallets
DEFAULT_CHAIN=ethereum
```

## 🔔 Webhook Notifications

Receive instant payment confirmations:

```bash
POST /webhook/callback
{
    "event": "payment.completed",
    "payment_id": "pay_abc123",
    "amount": 0.05,
    "currency": "ETH",
    "transaction_hash": "0x...",
    "timestamp": "2025-12-28T09:38:00Z"
}
```

## 📊 Dashboard

View all payments, invoices, and analytics:

```
GET /dashboard
```

Features:
- Real-time payment monitoring
- Revenue analytics
- Invoice management
- Transaction history
- Refund management

## 🔐 Security Features

- **Non-custodial**: Direct wallet payments
- **No frozen funds**: Instant settlements
- **Rate locking**: 15-minute rate protection
- **Signature verification**: Webhook security
- **Rate limiting**: DDoS protection

## 🚀 Deployment

### Docker
```bash
docker build -t crypto-pay .
docker run -p 8000:8000 crypto-pay
```

### Wasmer Edge
```bash
wasmer publish .
wasmer deploy
```

### Traditional Server
```bash
pip install -r requirements.txt
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📚 API Documentation

Full API reference available at: http://localhost:8000/docs

## 🤝 Support

- Documentation: /docs
- API Reference: /api/v1/docs
- Plugin Guides: /integration-plugins/

## 🎉 Start Accepting Crypto Today!

**No frozen funds. No approvals. Just direct payments to your wallet.**

```env
MERCHANT_WALLET=0x9646b67E78e81F88eb59177ec5a8c38fD2B0dcA2
ALTERNATIVE_WALLET=0xb549579a6d5ccfa3f8b143d11bcb4bf1494f7880
```
