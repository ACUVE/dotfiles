"""Bitwarden CLI integration for Docker credential storage.

Re-exports functions from the main docker_credential module.
"""

from ..docker_credential.bitwarden import (
    BitwardenError,
    check_bw_status,
    get_all_credentials,
    output_error,
    save_all_credentials,
)

__all__ = [
    "BitwardenError",
    "check_bw_status",
    "get_all_credentials",
    "output_error",
    "save_all_credentials",
]
