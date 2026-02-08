# CORS Setup Guide

If you're seeing connection errors between the frontend and backend, you need to enable CORS in your FastAPI backend.

## Quick Fix for FastAPI Backend

Add CORS middleware to your FastAPI app. In your `backend/app/main.py` (or wherever your FastAPI app is defined), add:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Your existing routes...
@app.get("/health")
async def health():
    return {"status": "ok"}

# ... rest of your routes
```

## Alternative: Allow All Origins (Development Only)

For development, you can allow all origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Only for development!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Verify Backend is Running

Make sure your backend is running:
```bash
cd ~/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then check: http://127.0.0.1:8000/docs

## Test Connection

After adding CORS, refresh your frontend at http://localhost:3000. You should see a green "Backend connected" message at the top.
