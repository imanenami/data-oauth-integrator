# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""Domain models definition module."""

from collections import namedtuple
from typing import Any, Literal

from pydantic import BaseModel

HealthStatus = Literal["ok", "error"]


TokenClaims = namedtuple("TokenClaims", "id_token, access_token")


class HealthResponse(BaseModel):
    """Response model for health check APIs."""

    status: HealthStatus


class IDTokenClaims(BaseModel):
    """Data model for `id_token.id_token_claims`."""

    jti: str
    iss: str
    sub: str
    aud: list[str]
    nonce: str
    at_hash: str
    acr: str
    amr: list[str] | None = None
    c_hash: str
    ext: dict[str, Any]


class IDTokenHeaders(BaseModel):
    """Data model for `id_token.headers`."""

    extra: dict[str, Any]


class IDToken(BaseModel):
    """Data model for `id_token`."""

    id_token_claims: IDTokenClaims
    headers: IDTokenHeaders
    username: str
    subject: str


class RequestSession(BaseModel):
    """Data model for `session` object in the POST request."""

    id_token: IDToken
    extra: dict[str, Any]
    client_id: str
    consent_challenge: str
    exclude_not_before_claim: bool
    allowed_top_level_claims: list[str]


class Request(BaseModel):
    """Data model for `request` object in the POST request."""

    client_id: str
    granted_scopes: list[str]
    granted_audience: list[str]
    grant_types: list[str]
    payload: dict


class RequestModel(BaseModel):
    """OAuth webhook request model."""

    session: RequestSession
    request: Request


class ResponseSession(BaseModel):
    """Data model for `session` object in the response."""

    access_token: dict[str, Any]
    id_token: dict[str, Any]


class ResponseModel(BaseModel):
    """OAuth webhook response model."""

    session: ResponseSession
