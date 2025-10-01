#!/usr/bin/env python3
"""
Start script for ANP Agent Example server.

This script properly sets up the Python path and starts the server.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set working directory to project root (not src)
os.chdir(project_root)

if __name__ == "__main__":
    import uvicorn


    print("🚀 Starting ANP Agent Example Server")
    print("=" * 40)
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source path: {src_path}")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print()

    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
