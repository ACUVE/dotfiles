"""Linux sandbox implementation using island (Landlock-based)."""

import os
import shlex
import shutil
import sys
import tempfile
from logging import getLogger
from pathlib import Path
from typing import Sequence

from .._common import collect_write_paths

_LOGGER = getLogger(__name__)


def _check_island_available() -> str:
    """Check if island is available and return its path.

    Raises:
        SystemExit: If island is not installed.
    """
    island_path = shutil.which("island")
    if island_path is None:
        print(
            "Error: island is not installed.\nInstall it with: mise install",
            file=sys.stderr,
        )
        sys.exit(1)
    return island_path


def _build_landlock_toml(
    read_only_paths: list[str],
    write_paths: list[str],
) -> str:
    """Build Landlock TOML configuration."""
    lines = []

    # ABI version is required for abi.* access groups
    lines.append("abi = 6")
    lines.append("")

    # Filter to existing paths only
    existing_ro_paths = [p for p in read_only_paths if os.path.exists(p)]
    existing_rw_paths = [p for p in write_paths if os.path.exists(p)]

    # Read-only paths (read + execute)
    if existing_ro_paths:
        lines.append("[[path_beneath]]")
        lines.append('allowed_access = ["abi.read_execute"]')
        paths_str = ", ".join(f'"{p}"' for p in existing_ro_paths)
        lines.append(f"parent = [{paths_str}]")
        lines.append("")

    # Read-write paths
    if existing_rw_paths:
        lines.append("[[path_beneath]]")
        lines.append('allowed_access = ["abi.read_write"]')
        paths_str = ", ".join(f'"{p}"' for p in existing_rw_paths)
        lines.append(f"parent = [{paths_str}]")
        lines.append("")

    return "\n".join(lines)


def _generate_profile(
    *,
    read_only_paths: list[str],
    write_paths: list[str],
) -> Path:
    """Generate a temporary island profile in island's config directory."""
    # island requires profiles to be in ~/.config/island/profiles/
    island_profiles_dir = Path.home() / ".config" / "island" / "profiles"
    island_profiles_dir.mkdir(parents=True, exist_ok=True)

    # Create a unique profile directory
    profile_dir = Path(tempfile.mkdtemp(prefix="sbx_", dir=island_profiles_dir))
    landlock_dir = profile_dir / "landlock"
    landlock_dir.mkdir()

    # profile.toml (empty is fine)
    (profile_dir / "profile.toml").write_text("")

    # landlock/base.toml
    landlock_config = _build_landlock_toml(read_only_paths, write_paths)
    (landlock_dir / "base.toml").write_text(landlock_config)

    return profile_dir


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
    """Execute a command in a sandboxed environment using island."""
    os.execvp(command[0], list(command))
    # currently no sandboxing on linux platforms

    island_path = _check_island_available()
    home = Path.home().as_posix()

    # Collect user-specified write paths
    user_write_paths = collect_write_paths(
        enable_git=enable_git,
        enable_cwd=enable_cwd,
        enable_awscli=enable_awscli,
        enable_cdk=enable_cdk,
        write=write,
    )

    # Default read-only paths (system directories)
    read_only_paths = [
        "/usr",
        "/bin",
        "/lib",
        "/lib64",
        "/sbin",
        "/etc",
        "/opt",
        # Home subdirectories that should be read-only
        # (excluding sensitive files by not including ~/.aws, ~/.zsh_history, etc.)
        os.path.join(home, ".config"),
        os.path.join(home, ".local/bin"),
        os.path.join(home, ".mise"),
        os.path.join(home, ".cargo"),
        os.path.join(home, ".rustup"),
    ]

    # Default write paths
    default_write_paths = [
        "/tmp",
        "/var/tmp",
        os.path.join(home, ".cache"),
        os.path.join(home, ".local/share"),
        os.path.join(home, ".npm"),
        os.path.join(home, ".pnpm"),
    ]

    # Combine write paths
    write_paths = default_write_paths + list(user_write_paths)

    # Generate temporary profile
    profile_dir = _generate_profile(
        read_only_paths=read_only_paths,
        write_paths=write_paths,
    )

    # Build island run command
    # -p takes the profile name (directory name), not full path
    profile_name = profile_dir.name
    cmd = [island_path, "run", "-p", profile_name, "--", *command]

    _LOGGER.info("Island profile: %s", profile_dir)
    _LOGGER.info("Island command: %s", shlex.join(cmd))

    if dry_run:
        landlock_config = (profile_dir / "landlock" / "base.toml").read_text()
        print(f"Profile directory: {profile_dir}")
        print(f"Landlock config:\n{landlock_config}")
        print(f"Command: {shlex.join(cmd)}")
        # Clean up in dry_run mode
        shutil.rmtree(profile_dir, ignore_errors=True)
    else:
        try:
            os.execvp(cmd[0], cmd)
        except Exception as e:
            # Clean up on error
            shutil.rmtree(profile_dir, ignore_errors=True)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
