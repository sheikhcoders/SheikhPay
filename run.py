"""
SheikhPay - Cryptocurrency Payment System
Entry point for Wasmer deployment
"""
import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and run the FastAPI application
from src.main import app

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8080))
    uvicorn.run(app, host=host, port=port)
