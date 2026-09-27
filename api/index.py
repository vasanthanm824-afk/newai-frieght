import sys
from pathlib import Path

# Add workspace root directory to python module lookup path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app

# Export FastAPI app for Vercel Serverless Function entrypoint
app = app
