#!/usr/bin/env python3
"""
Main entry point for Guardrails Server
"""
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=debug
    ) 