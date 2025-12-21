"""Bitwarden CLI integration for Docker credential helper."""

import json
import subprocess
import sys
from typing import Any

from .types import ErrorResponse


class BitwardenError(Exception):
    """Exception raised for Bitwarden-related errors."""

    pass


def check_bw_status() -> None:
    """
    Check if Bitwarden CLI is installed and unlocked.

    Raises:
        BitwardenError: If bw is not installed or is locked.
    """
    # Check if bw command exists
    result = subprocess.run(
        ["which", "bw"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BitwardenError("Bitwarden CLI (bw) is not installed")

    # Check if session is unlocked
    result = subprocess.run(
        ["bw", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BitwardenError(f"Failed to get Bitwarden status: {result.stderr}")

    try:
        status = json.loads(result.stdout)
        if status.get("status") != "unlocked":
            raise BitwardenError(
                "Bitwarden is locked. Please unlock with: export BW_SESSION=$(bw unlock --raw)"
            )
    except json.JSONDecodeError as e:
        raise BitwardenError(f"Failed to parse Bitwarden status: {e}")


def search_items(search_term: str) -> list[dict[str, Any]]:
    """
    Search for items in Bitwarden vault.

    Args:
        search_term: The search term to find items.

    Returns:
        List of items matching the search term.

    Raises:
        BitwardenError: If search fails or returns invalid data.
    """
    result = subprocess.run(
        ["bw", "list", "items", "--search", search_term],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BitwardenError(f"Failed to search Bitwarden items: {result.stderr}")

    try:
        items = json.loads(result.stdout)
        if not isinstance(items, list):
            raise BitwardenError("Invalid response from Bitwarden: expected a list")
        return items
    except json.JSONDecodeError as e:
        raise BitwardenError(f"Failed to parse Bitwarden response: {e}")


def output_error(message: str, exit_code: int = 1) -> None:
    """
    Output error in Docker credential helper format and exit.

    Args:
        message: Error message to output.
        exit_code: Exit code (default: 1).
    """
    error = ErrorResponse(error=message)
    print(error.model_dump_json(), file=sys.stderr)
    sys.exit(exit_code)


def list_items() -> list[dict[str, Any]]:
    """
    List all items in Bitwarden vault.

    Returns:
        List of all items in the vault.

    Raises:
        BitwardenError: If listing fails or returns invalid data.
    """
    result = subprocess.run(
        ["bw", "list", "items"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BitwardenError(f"Failed to list Bitwarden items: {result.stderr}")

    try:
        items = json.loads(result.stdout)
        if not isinstance(items, list):
            raise BitwardenError("Invalid response from Bitwarden: expected a list")
        return items
    except json.JSONDecodeError as e:
        raise BitwardenError(f"Failed to parse Bitwarden response: {e}")


def get_all_credentials(item_name: str) -> dict[str, Any]:
    """
    Get all credentials from a Bitwarden secure note item.

    Args:
        item_name: The name of the secure note item.

    Returns:
        Dictionary of credentials (server_url -> {Username, Secret}).

    Raises:
        BitwardenError: If reading from Bitwarden fails.
    """
    try:
        items = list_items()
    except BitwardenError:
        raise

    # Find the credentials item (type 2 = secure note)
    cred_item = None
    for item in items:
        if item.get("name") == item_name and item.get("type") == 2:
            cred_item = item
            break

    if not cred_item:
        return {}

    # Parse notes field as JSON
    notes = cred_item.get("notes", "{}")

    try:
        credentials = json.loads(notes)
        if not isinstance(credentials, dict):
            return {}
        return credentials
    except json.JSONDecodeError:
        return {}


def save_all_credentials(item_name: str, credentials: dict[str, Any]) -> None:
    """
    Save all credentials to a Bitwarden secure note item.

    Args:
        item_name: The name of the secure note item.
        credentials: Dictionary of credentials to save.

    Raises:
        BitwardenError: If saving to Bitwarden fails.
    """
    credentials_json = json.dumps(credentials)

    try:
        items = list_items()
    except BitwardenError:
        raise

    # Find existing item
    item_id = None
    for item in items:
        if item.get("name") == item_name and item.get("type") == 2:
            item_id = item.get("id")
            break

    if item_id:
        # Update existing item
        # Read current item to preserve other fields
        result = subprocess.run(
            ["bw", "get", "item", item_id],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise BitwardenError(f"Failed to get item: {result.stderr}")

        try:
            current_item = json.loads(result.stdout)
            current_item["notes"] = credentials_json

            # Encode and update
            encode_result = subprocess.run(
                ["bw", "encode"],
                input=json.dumps(current_item),
                capture_output=True,
                text=True,
                check=False,
            )
            if encode_result.returncode != 0:
                raise BitwardenError(f"Failed to encode item: {encode_result.stderr}")

            update_result = subprocess.run(
                ["bw", "edit", "item", item_id],
                input=encode_result.stdout,
                capture_output=True,
                text=True,
                check=False,
            )
            if update_result.returncode != 0:
                raise BitwardenError(f"Failed to update item: {update_result.stderr}")
        except json.JSONDecodeError as e:
            raise BitwardenError(f"Failed to parse item: {e}")
    else:
        # Create new secure note item
        new_item = {
            "type": 2,
            "name": item_name,
            "notes": credentials_json,
            "secureNote": {"type": 0},
        }

        # Encode and create
        encode_result = subprocess.run(
            ["bw", "encode"],
            input=json.dumps(new_item),
            capture_output=True,
            text=True,
            check=False,
        )
        if encode_result.returncode != 0:
            raise BitwardenError(f"Failed to encode item: {encode_result.stderr}")

        create_result = subprocess.run(
            ["bw", "create", "item"],
            input=encode_result.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        if create_result.returncode != 0:
            raise BitwardenError(f"Failed to create item: {create_result.stderr}")

    # Sync (ignore errors)
    subprocess.run(
        ["bw", "sync"],
        capture_output=True,
        check=False,
    )
