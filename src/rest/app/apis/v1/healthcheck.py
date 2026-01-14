# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""Healthcheck API routes."""

from app.core.models import HealthResponse
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/readiness")
async def readiness(_: Request) -> HealthResponse:
    """Readiness Probe."""
    return HealthResponse(status="ok")


@router.get("/liveness")
async def liveness(_: Request) -> HealthResponse:
    """Liveness Probe."""
    return HealthResponse(status="ok")
