"""Pydantic models for Docker credential helper."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class DockerCredential(BaseModel):
    """Docker credential helper output format for get command."""

    ServerURL: Annotated[str, Field(description="Docker registry server URL")]
    Username: Annotated[
        str, Field(min_length=1, description="Username for authentication")
    ]
    Secret: Annotated[str, Field(min_length=1, description="Password or token")]

    @field_validator("ServerURL")
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        """Validate that ServerURL is not empty."""
        if not v:
            raise ValueError("ServerURL cannot be empty")
        return v


class DockerCredentialInput(BaseModel):
    """Docker credential helper input format for store command."""

    ServerURL: Annotated[str, Field(description="Docker registry server URL")]
    Username: Annotated[
        str, Field(min_length=1, description="Username for authentication")
    ]
    Secret: Annotated[str, Field(min_length=1, description="Password or token")]


class ErrorResponse(BaseModel):
    """Error response format for Docker credential helper."""

    error: Annotated[str, Field(description="Error message")]
