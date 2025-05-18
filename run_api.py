#!/usr/bin/env python3
"""
Run the FastAPI server for The Living Rusted Tankard.
"""
import uvicorn
from core.api import app

if __name__ == "__main__":
    uvicorn.run(
        "core.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
