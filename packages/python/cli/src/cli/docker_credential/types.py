"""Pydantic models for Docker credential helper."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BitwardenLogin(BaseModel):
    """Bitwarden login item credentials.

    This model represents the login credentials stored in a Bitwarden login item.
    Unknown fields from the Bitwarden CLI API response are ignored to maintain
    compatibility with different Bitwarden CLI versions.
    """

    model_config = ConfigDict(extra="ignore")

    username: Annotated[str, Field(description="Username for authentication")]
    password: Annotated[str, Field(description="Password for authentication")]


class BitwardenSecureNote(BaseModel):
    """Bitwarden secure note metadata.

    This model represents the metadata for a Bitwarden secure note item.
    Unknown fields from the Bitwarden CLI API response are ignored to maintain
    compatibility with different Bitwarden CLI versions.

    Secure note types:
        0: Generic secure note
    """

    model_config = ConfigDict(extra="ignore")

    type: Annotated[int, Field(default=0, description="Secure note type")]


class BitwardenItem(BaseModel):
    """Bitwarden vault item from CLI API response.

    This model represents a Bitwarden vault item as returned by the Bitwarden CLI.
    It supports both login items (type 1) and secure note items (type 2).
    Unknown fields from the Bitwarden CLI API response are ignored to maintain
    compatibility with different Bitwarden CLI versions.

    Item types:
        1: Login item (contains login credentials)
        2: Secure note item (contains notes field with arbitrary text)
    """

    model_config = ConfigDict(extra="ignore")

    id: Annotated[str, Field(description="Unique identifier for the item")]
    name: Annotated[str, Field(description="Display name of the item")]
    type: Annotated[int, Field(description="Item type (1=login, 2=secure note)")]
    notes: Annotated[str | None, Field(default=None, description="Notes field content")]
    login: Annotated[
        BitwardenLogin | None,
        Field(default=None, description="Login credentials (for type 1 items)"),
    ]
    secureNote: Annotated[
        BitwardenSecureNote | None,
        Field(default=None, description="Secure note metadata (for type 2 items)"),
    ]


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
