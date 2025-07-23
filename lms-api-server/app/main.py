from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_onboarding, routes_inference

app = FastAPI(
    title="LMS API Server",
    description="Handles onboarding and inference requests for Evolving AI LMS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_onboarding.router)
app.include_router(routes_inference.router)
