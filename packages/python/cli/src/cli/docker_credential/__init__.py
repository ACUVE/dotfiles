"""Docker credential helper using Bitwarden CLI.

This module implements the Docker credential helper specification for Bitwarden.
It provides read-only access to Docker Hub credentials stored in Bitwarden.

Supported commands:
- get: Retrieve credentials for a server URL
- store: Accept credentials (no-op, read-only implementation)
- erase: Erase credentials (no-op, read-only implementation)
- list: List all stored credentials
"""

import json
import sys
from typing import Any

from pydantic import ValidationError

from .bitwarden import BitwardenError, check_bw_status, output_error, search_items
from .types import DockerCredential, DockerCredentialInput

# Constants
_DOCKER_HUB_URL = "https://index.docker.io/v1/"


def _cmd_get(server_url: str, search_term: str) -> None:
    """
    Get credentials for a server URL.

    Args:
        server_url: The Docker registry server URL.
        search_term: The search term to find credentials in Bitwarden.
    """
    # Only handle Docker Hub
    if server_url != _DOCKER_HUB_URL:
        output_error(f"credentials not found for {server_url}")
        return  # For type checker (output_error calls sys.exit)

    try:
        check_bw_status()
        items = search_items(search_term)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    if not items:
        output_error("credentials not found")
        return  # For type checker (output_error calls sys.exit)

    # Parse the first matching item
    first_item = items[0]
    login = first_item.get("login", {})
    username = login.get("username")
    password = login.get("password")

    if not username or not password:
        output_error("invalid credentials format")
        return  # For type checker (output_error calls sys.exit)

    # Create and validate the credential
    try:
        credential = DockerCredential(
            ServerURL=server_url,
            Username=username,
            Secret=password,
        )
        print(credential.model_dump_json())
    except ValidationError as e:
        output_error(f"validation error: {e.errors()[0]['msg']}")
        return  # For type checker (output_error calls sys.exit)


def _cmd_store(input_data: dict[str, Any]) -> None:
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


def _cmd_erase(server_url: str) -> None:
    """
    Erase credentials (no-op implementation).

    This is a read-only implementation that accepts the server URL but does not
    actually erase credentials from Bitwarden.

    Args:
        server_url: The Docker registry server URL to erase credentials for.
    """
    # Silently succeed without updating Bitwarden
    sys.exit(0)


def _cmd_list(search_term: str) -> None:
    """
    List all stored credentials.

    Args:
        search_term: The search term to find credentials in Bitwarden.
    """
    try:
        check_bw_status()
        items = search_items(search_term)
    except BitwardenError as e:
        output_error(str(e))
        return  # For type checker (output_error calls sys.exit)

    if not items:
        print("{}")
        sys.exit(0)
        return  # For type checker (sys.exit is mocked in tests)

    # Get username from the first matching item
    first_item = items[0]
    login = first_item.get("login", {})
    username = login.get("username")

    if not username:
        print("{}")
    else:
        result = {_DOCKER_HUB_URL: username}
        print(json.dumps(result))


def main(command: str, search_term: str = "DockerHub") -> None:
    """
    Main entry point for docker-credential-bw-docker.

    Args:
        command: The command to execute (get, store, erase, list).
        search_term: The search term for Bitwarden lookup (default: "DockerHub").
    """
    if command == "get":
        server_url = sys.stdin.read().strip()
        _cmd_get(server_url, search_term)
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
        _cmd_list(search_term)
    else:
        output_error(
            f"Unknown command: {command}. Supported commands: get, store, erase, list"
        )
