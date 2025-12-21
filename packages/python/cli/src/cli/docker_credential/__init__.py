"""Docker credential helper using Bitwarden CLI.

This module implements the Docker credential helper specification for Bitwarden.
It provides both read-only access to Docker Hub credentials stored in Bitwarden,
and full read-write access to credentials stored in a secure note.

Supported commands:
- get: Retrieve credentials for a server URL
- store: Accept credentials (no-op for docker-bw-docker, full storage for docker-bw)
- erase: Erase credentials (no-op for docker-bw-docker, full erase for docker-bw)
- list: List all stored credentials
"""

import json
import sys
from typing import Literal, NoReturn

from pydantic import ValidationError

from .bitwarden import (
    BitwardenError,
    check_bw_status,
    get_all_credentials,
    output_error,
    save_all_credentials,
    search_items,
)
from .types import DockerCredential, DockerCredentialInput

# Constants
_DOCKER_HUB_URL = "https://index.docker.io/v1/"
_ITEM_NAME = "docker-credentials"


def _cmd_get_docker_hub(server_url: str, search_term: str) -> None:
    """
    Get credentials for Docker Hub from Bitwarden search.

    Args:
        server_url: The Docker registry server URL.
        search_term: The search term to find credentials in Bitwarden.
    """
    # Only handle Docker Hub
    if server_url != _DOCKER_HUB_URL:
        output_error(f"credentials not found for {server_url}")

    try:
        check_bw_status()
        items = search_items(search_term)
    except BitwardenError as e:
        output_error(str(e))

    if not items:
        output_error("credentials not found")

    # Parse the first matching item
    first_item = items[0]
    login = first_item.login

    if not login or not login.username or not login.password:
        output_error("invalid credentials format")

    # Create and validate the credential
    try:
        credential = DockerCredential(
            ServerURL=server_url,
            Username=login.username,
            Secret=login.password,
        )
        print(credential.model_dump_json())
    except ValidationError as e:
        output_error(f"validation error: {e.errors()[0]['msg']}")


def _cmd_get_storage(server_url: str) -> None:
    """
    Get credentials for a server URL from storage.

    Args:
        server_url: The server URL to get credentials for.
    """
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))

    # Extract credential for the requested server URL
    cred_data = all_creds.get(server_url)

    if not cred_data:
        output_error("credentials not found")

    # Parse credential
    username = cred_data.get("Username")
    secret = cred_data.get("Secret")

    if not username or not secret:
        output_error("invalid credentials format")

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


def _cmd_store_noop(input_data: dict[str, str]) -> NoReturn:
    """
    Store credentials (no-op implementation).

    This is a read-only implementation that validates input but does not
    actually store credentials in Bitwarden.

    Args:
        input_data: The credential data to store.
    """
    try:
        # Validate input format
        DockerCredentialInput(**input_data)
        # Silently succeed without updating Bitwarden
        sys.exit(0)
    except ValidationError as e:
        output_error(f"invalid input: {e.errors()[0]['msg']}")


def _cmd_store_storage(input_data: dict[str, str]) -> NoReturn:
    """
    Store credentials for a server URL in storage.

    Args:
        input_data: The credential data to store.
    """
    # Validate input format
    try:
        cred_input = DockerCredentialInput(**input_data)
    except ValidationError as e:
        output_error(f"invalid input: {e.errors()[0]['msg']}")

    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))

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


def _cmd_erase_noop(server_url: str) -> NoReturn:
    """
    Erase credentials (no-op implementation).

    This is a read-only implementation that accepts the server URL but does not
    actually erase credentials from Bitwarden.

    Args:
        server_url: The Docker registry server URL to erase credentials for.
    """
    # Silently succeed without updating Bitwarden
    sys.exit(0)


def _cmd_erase_storage(server_url: str) -> NoReturn:
    """
    Erase credentials for a server URL from storage.

    Args:
        server_url: The server URL to erase credentials for.
    """
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))

    # Check if the credential exists
    if server_url not in all_creds:
        # No credential to delete, succeed silently
        sys.exit(0)

    # Remove the credential for this server URL
    del all_creds[server_url]

    # Save back to Bitwarden
    try:
        save_all_credentials(_ITEM_NAME, all_creds)
        sys.exit(0)
    except BitwardenError as e:
        output_error(str(e))


def _cmd_list_docker_hub(search_term: str) -> None:
    """
    List Docker Hub credentials from Bitwarden search.

    Args:
        search_term: The search term to find credentials in Bitwarden.
    """
    try:
        check_bw_status()
        items = search_items(search_term)
    except BitwardenError as e:
        output_error(str(e))

    if not items:
        print("{}")
        sys.exit(0)

    # Get username from the first matching item
    first_item = items[0]
    login = first_item.login

    if not login or not login.username:
        print("{}")
    else:
        result = {_DOCKER_HUB_URL: login.username}
        print(json.dumps(result))


def _cmd_list_storage() -> NoReturn:
    """List all stored credentials from storage."""
    try:
        check_bw_status()
        all_creds = get_all_credentials(_ITEM_NAME)
    except BitwardenError as e:
        output_error(str(e))

    # Convert to the list format: {"url": "username", ...}
    result = {url: cred["Username"] for url, cred in all_creds.items()}

    print(json.dumps(result))
    sys.exit(0)


def docker_credential_bw(command: Literal["get", "store", "erase", "list"]) -> None:
    """
    Main entry point for docker-credential-bw.

    Args:
        command: The command to execute (get, store, erase, list).
    """
    if command == "get":
        server_url = sys.stdin.read().strip()
        _cmd_get_storage(server_url)
    elif command == "store":
        input_json = sys.stdin.read().strip()
        try:
            input_data = json.loads(input_json)
        except json.JSONDecodeError as e:
            output_error(f"invalid JSON input: {e}")
            return  # For type checker (output_error calls sys.exit)
        _cmd_store_storage(input_data)
    elif command == "erase":
        server_url = sys.stdin.read().strip()
        _cmd_erase_storage(server_url)
    elif command == "list":
        _cmd_list_storage()
    else:
        output_error(
            f"Unknown command: {command}. Supported commands: get, store, erase, list"
        )


def docker_credential_bw_docker(
    command: Literal["get", "store", "erase", "list"], search_term: str = "DockerHub"
) -> None:
    """
    Main entry point for docker-credential-bw-docker.

    Args:
        command: The command to execute (get, store, erase, list).
        search_term: The search term for Bitwarden lookup (default: "DockerHub").
    """
    if command == "get":
        server_url = sys.stdin.read().strip()
        _cmd_get_docker_hub(server_url, search_term)
    elif command == "store":
        input_json = sys.stdin.read().strip()
        try:
            input_data = json.loads(input_json)
        except json.JSONDecodeError as e:
            output_error(f"invalid JSON input: {e}")
        _cmd_store_noop(input_data)
    elif command == "erase":
        server_url = sys.stdin.read().strip()
        _cmd_erase_noop(server_url)
    elif command == "list":
        _cmd_list_docker_hub(search_term)
    else:
        output_error(
            f"Unknown command: {command}. Supported commands: get, store, erase, list"
        )
