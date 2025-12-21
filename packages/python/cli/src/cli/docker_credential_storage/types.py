"""Type definitions for Docker credential storage.

Re-exports types from the main docker_credential module.
"""

from ..docker_credential.types import (
    DockerCredential,
    DockerCredentialInput,
    ErrorResponse,
)

__all__ = ["DockerCredential", "DockerCredentialInput", "ErrorResponse"]
