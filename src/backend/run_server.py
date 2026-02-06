#!/usr/bin/env python
"""
Server launcher script.
Run this file to start the FastAPI development server.
"""
import sys
from pathlib import Path

# Add src to path to ensure imports work
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(src_dir), str(backend_dir.parent / "data")]
    )
