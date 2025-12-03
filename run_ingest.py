"""
Simple launcher script for the Ingest API.
Run from project root: python run_ingest.py
"""
import os
import sys

# Set working directory to ingest-api
os.chdir(os.path.join(os.path.dirname(__file__), "services", "ingest-api"))
sys.path.insert(0, os.getcwd())

# Now import and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["."]
    )
