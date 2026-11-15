import sys
import os

# Add backend directory to Python path so 'app' module is found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Import and re-export the FastAPI app
from app.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
