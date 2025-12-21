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
