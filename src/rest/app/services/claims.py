# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""Service (controller) implementation for claims management."""

from app.core.models import RequestModel, TokenClaims


def process_claims(r: RequestModel) -> TokenClaims:
    """Process OAuth2 claims for an incoming request."""
    return TokenClaims(
        id_token={"dpe:roleClaim": "admin"},
        access_token={"dpe:roleClaim": "admin"},
    )
