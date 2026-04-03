#!/usr/bin/env python3
"""
Start script for Quran Shield application
"""
import os
import sys
import uvicorn


def main():
    """Start the FastAPI server"""
    # Change to backend directory if not already there
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        sys.path.insert(0, backend_dir)
    
    # Start server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
