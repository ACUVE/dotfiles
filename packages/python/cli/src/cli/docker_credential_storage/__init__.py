"""Docker credential helper using Bitwarden storage.

This module implements the Docker credential helper specification using
Bitwarden CLI to store all credentials in a single secure note item.
"""

import json
import sys
from typing import Any

from pydantic import ValidationError

from .bitwarden import (
    BitwardenError,
    check_bw_status,
    get_all_credentials,
    output_error,
    save_all_credentials,
)
from .types import DockerCredential, DockerCredentialInput

# Constants
_ITEM_NAME = "docker-credentials"


def _cmd_get(server_url: str) -> None:
    """
    Get credentials for a server URL.

    Args:
        server_url: The server URL to get credentials for.
    """
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    # Extract credential for the requested server URL
    cred_data = all_creds.get(server_url)

    if not cred_data:
        output_error("credentials not found")
        return  # For type checker (output_error calls sys.exit)

    # Parse credential
    username = cred_data.get("Username")
    secret = cred_data.get("Secret")

    if not username or not secret:
        output_error("invalid credentials format")
        return  # For type checker (output_error calls sys.exit)

    # Create and validate the credential
    try:
        credential = DockerCredential(
            ServerURL=server_url,
            Username=username,
            Secret=secret,
        )
        print(credential.model_dump_json())
    except ValidationError as e:
        output_error(f"validation error: {e.errors()[0]['msg']}")
        return  # For type checker (output_error calls sys.exit)


def _cmd_store(input_data: dict[str, Any]) -> None:
    """
    Store credentials for a server URL.

    Args:
        input_data: The credential data to store.
    """
    # Validate input format
    try:
        cred_input = DockerCredentialInput(**input_data)
    except ValidationError as e:
        output_error(f"invalid input: {e.errors()[0]['msg']}")
        return  # For type checker (output_error calls sys.exit)

    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    # Add or update the credential for this server URL
    all_creds[cred_input.ServerURL] = {
        "Username": cred_input.Username,
        "Secret": cred_input.Secret,
    }

    # Save back to Bitwarden
    try:
        save_all_credentials(_ITEM_NAME, all_creds)
        sys.exit(0)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)


def _cmd_erase(server_url: str) -> None:
    """
    Erase credentials for a server URL.

    Args:
        server_url: The server URL to erase credentials for.
    """
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    # Check if the credential exists
    if server_url not in all_creds:
        # No credential to delete, succeed silently
        sys.exit(0)
        return  # For type checker

    # Remove the credential for this server URL
    del all_creds[server_url]

    # Save back to Bitwarden
    try:
        save_all_credentials(_ITEM_NAME, all_creds)
        sys.exit(0)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)


def _cmd_list() -> None:
    """List all stored credentials."""
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    # Convert to the list format: {"url": "username", ...}
    result = {url: cred["Username"] for url, cred in all_creds.items()}

    print(json.dumps(result))
    sys.exit(0)


def docker_credential_bw(command: str) -> None:
    """
    Main entry point for docker-credential-bw.

    Args:
        command: The command to execute (get, store, erase, list).
    """
    if command == "get":
        server_url = sys.stdin.read().strip()
        _cmd_get(server_url)
    elif command == "store":
        input_json = sys.stdin.read().strip()
        try:
            input_data = json.loads(input_json)
        except json.JSONDecodeError as e:
            output_error(f"invalid JSON input: {e}")
            return  # For type checker (output_error calls sys.exit)
        _cmd_store(input_data)
    elif command == "erase":
        server_url = sys.stdin.read().strip()
        _cmd_erase(server_url)
    elif command == "list":
        _cmd_list()
    else:
        output_error(
            f"Unknown command: {command}. Supported commands: get, store, erase, list"
        )
        return  # For type checker (output_error calls sys.exit)
