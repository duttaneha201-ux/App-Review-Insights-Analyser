"""
FastAPI server for handling API requests

Run with: uvicorn app.api.server:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.subscriptions import (
    create_subscription,
    SubscriptionRequest,
    SubscriptionResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="App Review Insights API",
    description="API for managing app review analysis subscriptions",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "App Review Insights API"}


@app.post("/api/subscriptions", response_model=SubscriptionResponse)
async def post_subscription(request: SubscriptionRequest):
    """
    Create a new subscription and trigger analysis.
    
    Request body:
    {
        "playstore_url": "https://play.google.com/store/apps/details?id=com.example",
        "weeks": 8,
        "email": "user@example.com"
    }
    
    Response:
    {
        "status": "success",
        "message": "Analysis started. You will receive the insights by email.",
        "app_id": "com.example"
    }
    """
    return await create_subscription(request)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}








