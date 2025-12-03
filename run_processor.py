"""
Launcher script for the Processor Worker.
Run from project root: python run_processor.py
"""
import os
import sys
import asyncio

# Set working directory to processor
os.chdir(os.path.join(os.path.dirname(__file__), "services", "processor"))
sys.path.insert(0, os.getcwd())

import main

if __name__ == "__main__":
    asyncio.run(main.main())
