"""
Launcher script for the UI Backend API.
Run from project root: python run_ui_backend.py
"""
import os
import sys

# Set working directory to ui-backend
os.chdir(os.path.join(os.path.dirname(__file__), "services", "ui-backend"))
sys.path.insert(0, os.getcwd())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["."]
    )
