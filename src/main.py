"""
Cryptocurrency Payment System - FastAPI Application
Non-custodial payments directly to your wallet - no frozen funds!
"""
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import routers
from src.routes.payments import router as payments_router
from src.routes.invoices import router as invoices_router
from src.routes.links import router as links_router
from src.routes.webhooks import router as webhooks_router
from src.routes.integrations import router as integrations_router
from src.services.blockchain import blockchain_service

# Application configuration
APP_VERSION = "2.0.0"
MERCHANT_WALLET = os.getenv("MERCHANT_WALLET", "0x9646b67E78e81F88eb59177ec5a8c38fD2B0dcA2")
ALTERNATIVE_WALLET = os.getenv("ALTERNATIVE_WALLET", "0xb549579a6d5ccfa3f8b143d11bcb4bf1494f7880")
DEFAULT_CHAIN = os.getenv("DEFAULT_CHAIN", "ethereum")
NETWORK_ENV = os.getenv("NETWORK_ENV", "PRODUCTION")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print(f"🚀 Starting CryptoPay System v{APP_VERSION}")
    print(f"🌐 Network: {NETWORK_ENV}")
    print(f"💰 Primary Wallet: {MERCHANT_WALLET}")
    print(f"💰 Alternative Wallet: {ALTERNATIVE_WALLET}")
    print(f"⛓️ Default Chain: {DEFAULT_CHAIN}")
    
    # Start blockchain monitoring
    await blockchain_service.start_monitoring()
    
    yield
    
    print("🛑 Shutting down CryptoPay System...")
    await blockchain_service.stop_monitoring()

# Create FastAPI application
app = FastAPI(
    title="CryptoPay - Cryptocurrency Payment System",
    description="Non-custodial cryptocurrency payment processor with invoicing, payment links, and e-commerce integrations",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="src/templates")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Check system health."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "network": NETWORK_ENV,
        "wallets": {
            "primary": MERCHANT_WALLET,
            "alternative": ALTERNATIVE_WALLET
        },
        "default_chain": DEFAULT_CHAIN,
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CryptoPay - Cryptocurrency Payment System",
        "version": APP_VERSION,
        "description": "Non-custodial payments directly to your wallet",
        "features": [
            "Direct wallet payments (no frozen funds)",
            "Multi-chain support (ETH, BSC, Polygon, Arbitrum)",
            "Payment links and invoices",
            "E-commerce integrations (WooCommerce, Shopify, WHMCS)",
            "Telegram Mini App support"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "dashboard": "/dashboard",
            "payments": "/api/v1/payments",
            "invoices": "/api/v1/invoices",
            "links": "/api/v1/links"
        },
        "wallets": {
            "primary": MERCHANT_WALLET,
            "alternative": ALTERNATIVE_WALLET
        }
    }

# Dashboard endpoint
@app.get("/dashboard", tags=["dashboard"])
async def dashboard(request: Request):
    """Merchant dashboard."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "version": APP_VERSION,
        "merchant_wallet": MERCHANT_WALLET,
        "alternative_wallet": ALTERNATIVE_WALLET
    })

# Include routers
app.include_router(payments_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")
app.include_router(links_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if NETWORK_ENV == "SANDBOX" else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
