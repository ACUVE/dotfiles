"""Sandbox execution module.

Provides sandboxed command execution:
- macOS: Uses sandbox-exec

Other platforms (Linux, Windows) are not implemented and raise
NotImplementedError.
"""

import sys
from typing import Sequence

from .darwin import sbx as darwin_sbx


def sbx(
    *,
    enable_git: bool,
    enable_cwd: bool,
    enable_awscli: bool,
    enable_cdk: bool,
    write: Sequence[str],
    deny_read: Sequence[str],
    dry_run: bool,
    command: Sequence[str],
) -> None:
    """Execute a command in a sandboxed environment.

    Args:
        enable_git: Allow write access to git repository and .git directory.
        enable_cwd: Allow write access to current working directory.
        enable_awscli: Allow write access to ~/.aws directory.
        enable_cdk: Allow write access to ~/.cdk directory.
        write: Additional directories to allow write access.
        dry_run: Print the sandbox command without executing.
        command: The command to execute in the sandbox.

    Raises:
        NotImplementedError: If the current platform is not supported.
    """
    if sys.platform != "darwin":
        raise NotImplementedError(
            f"Sandbox execution is not supported on {sys.platform}. "
            "Supported platforms: darwin (macOS) only."
        )

    sbx_impl = darwin_sbx
    sbx_impl(
        enable_git=enable_git,
        enable_cwd=enable_cwd,
        enable_awscli=enable_awscli,
        enable_cdk=enable_cdk,
        write=write,
        deny_read=deny_read,
        dry_run=dry_run,
        command=command,
    )
