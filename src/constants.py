"""Constants used across the codebase."""

from typing import Literal

CHARM_KEY = "data-oauth-integrator"
REST_PORT = 8080
SERVICE_NAME = "oauth-webhook"
SERVICE_PATH = ""

Substrates = Literal["vm", "k8s"]
SUBSTRATE: Substrates = "vm"

PEER_REL = "peer"
