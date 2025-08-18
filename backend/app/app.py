"""
Application entry point for the Prompt Manager backend.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from .__init__ import app


if __name__ == "__main__":
    # Run with: python app.py
    uvicorn.run(
        "app:app",          # module:app_instance
        host="0.0.0.0",     # accessible externally
        port=8000,
        reload=False,       # disable auto-reload
        workers=4           # number of worker processes
    )
