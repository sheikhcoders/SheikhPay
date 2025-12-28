"""
Entry point for SheikhPay on Wasmer Python runtime
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from src.main import app as application

# Export for wasmer
__all__ = ["application"]
