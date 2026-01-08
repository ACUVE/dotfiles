"""Linux sandbox implementation using bubblewrap (bwrap)."""

import os
import shlex
import shutil
import sys
from logging import getLogger
from pathlib import Path
from typing import Sequence

from .._common import collect_write_paths

_LOGGER = getLogger(__name__)

# System directories to bind read-only by default
_DEFAULT_RO_BINDS = [
    "/usr",
    "/bin",
    "/lib",
    "/lib64",
    "/sbin",
    "/etc",
    "/opt",
]

# Paths that should be read-write by default
_DEFAULT_RW_PATHS = [
    "/tmp",
    "/var/tmp",
]


def _check_bwrap_available() -> str:
    """Check if bwrap is available and return its path.

    Raises:
        SystemExit: If bwrap is not installed.
    """
    bwrap_path = shutil.which("bwrap")
    if bwrap_path is None:
        print(
            "Error: bubblewrap (bwrap) is not installed.\n"
            "Install it with:\n"
            "  Ubuntu/Debian: sudo apt install bubblewrap\n"
            "  Fedora: sudo dnf install bubblewrap\n"
            "  Arch: sudo pacman -S bubblewrap",
            file=sys.stderr,
        )
        sys.exit(1)
    return bwrap_path


def _build_bwrap_command(
    *,
    write_paths: list[str],
    command: Sequence[str],
) -> list[str]:
    """Build the bwrap command with appropriate bindings."""
    bwrap_path = _check_bwrap_available()
    home = Path.home().as_posix()
    cwd = os.getcwd()

    cmd = [bwrap_path]

    # Create new PID namespace
    cmd.extend(["--unshare-pid"])

    # Mount /proc and /dev
    cmd.extend(["--proc", "/proc"])
    cmd.extend(["--dev", "/dev"])

    # Bind system directories read-only
    for path in _DEFAULT_RO_BINDS:
        if os.path.exists(path):
            cmd.extend(["--ro-bind", path, path])

    # Temporary directories are read-write
    for path in _DEFAULT_RW_PATHS:
        if os.path.exists(path):
            cmd.extend(["--bind", path, path])

    # Home directory is read-only by default
    cmd.extend(["--ro-bind", home, home])

    # Cache directories under home should be writable
    cache_dirs = [
        os.path.join(home, ".cache"),
        os.path.join(home, ".local/share"),
        os.path.join(home, ".npm"),
        os.path.join(home, ".pnpm"),
    ]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            cmd.extend(["--bind", cache_dir, cache_dir])

    # User-specified write paths
    for path in write_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            cmd.extend(["--bind", abs_path, abs_path])
        else:
            _LOGGER.warning("Write path does not exist: %s", abs_path)

    # Mask sensitive files with tmpfs (similar to macOS deny file-read-data)
    # This prevents reading shell history
    sensitive_files = [
        os.path.join(home, ".zsh_history"),
        os.path.join(home, ".bash_history"),
    ]
    for sensitive_file in sensitive_files:
        if os.path.exists(sensitive_file):
            cmd.extend(["--tmpfs", sensitive_file])

    # Note: ~/.aws/credentials is accessible because home is ro-bind mounted.
    # Unlike macOS sandbox-exec which can deny file-read-data specifically,
    # bubblewrap doesn't have fine-grained read permission control.
    # If you need to restrict it, you would need to not bind $HOME and instead
    # bind only specific subdirectories.

    # Change to current working directory
    cmd.extend(["--chdir", cwd])

    # Add the command to execute
    cmd.append("--")
    cmd.extend(command)

    return cmd


def sbx(
    *,
    enable_git: bool,
    enable_cwd: bool,
    enable_awscli: bool,
    enable_cdk: bool,
    write: Sequence[str],
    dry_run: bool,
    command: Sequence[str],
) -> None:
    """Execute a command in a sandboxed environment using bubblewrap."""
    write_paths = collect_write_paths(
        enable_git=enable_git,
        enable_cwd=enable_cwd,
        enable_awscli=enable_awscli,
        enable_cdk=enable_cdk,
        write=write,
    )

    cmd = _build_bwrap_command(
        write_paths=write_paths,
        command=command,
    )

    _LOGGER.info("Bubblewrap command: %s", shlex.join(cmd))

    try:
        if dry_run:
            print(" ".join(shlex.quote(arg) for arg in cmd))
        else:
            os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
