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

    from config import HOST, LOG_LEVEL, PORT, RELOAD

    print("🚀 Starting ANP Agent Example Server")
    print("=" * 40)
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source path: {src_path}")
    print(f"🌐 Server will be available at: http://{HOST}:{PORT}")
    print(f"📚 API docs will be available at: http://localhost:{PORT}/docs")
    print()

    # Start the server
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level=LOG_LEVEL.lower()
    )
