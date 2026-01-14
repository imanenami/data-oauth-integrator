# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""API routes definition."""

from app.apis.v1 import healthcheck, oauth2
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(healthcheck.router, prefix="/healthcheck", tags=["healthcheck"])
api_router.include_router(oauth2.router, prefix="/oauth2", tags=["oauth2"])
