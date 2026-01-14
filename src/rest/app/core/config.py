# Copyright 2026 Iman DA
# See LICENSE file for licensing details.

"""FastAPI configuration module."""

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration object."""

    PROJECT_NAME: str = "Custom OAuth WebHook"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        """Configuration for environment variable overrides."""

        case_sensitive: bool = True
        env_file: str = ".env"


settings = Settings()
