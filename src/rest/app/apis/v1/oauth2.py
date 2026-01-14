# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""Plugin API routes definition."""

from app.core.models import RequestModel, ResponseModel, ResponseSession
from app.services.claims import process_claims
from fastapi import APIRouter

router = APIRouter()


@router.post("/hook")
async def claims_hook(r: RequestModel) -> ResponseModel:
    """Handle claims for an incoming request."""
    print(r.request.client_id)
    claims = process_claims(r)

    return ResponseModel(
        session=ResponseSession(
            access_token=claims.access_token,
            id_token=claims.id_token,
        )
    )
