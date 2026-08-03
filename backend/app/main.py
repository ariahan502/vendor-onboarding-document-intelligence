from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings


app = FastAPI(
    title="Vendor Onboarding Document Intelligence API",
    version="0.1.0",
    description=(
        "Backend API for vendor packet review, validation findings, "
        "review decisions, and evaluation workflows."
    ),
)

# Fail during startup rather than serving a production process with local-only state.
settings.validate_production_configuration()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
