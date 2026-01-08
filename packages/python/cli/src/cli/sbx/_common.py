"""Common utilities for sandbox implementations."""

import os
import shlex
import subprocess
from logging import DEBUG, getLogger
from pathlib import Path
from typing import Sequence

_LOGGER = getLogger(__name__)


def call_command(cmd: Sequence[str]) -> str:
    """Execute a command and return its output as a string."""
    if _LOGGER.isEnabledFor(DEBUG):
        _LOGGER.debug("Executing command: %s", shlex.join(cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    stdout = result.stdout.strip()
    _LOGGER.debug("Command output: %s", stdout)
    return stdout


def git_subpaths() -> list[str]:
    """Get git repository root and .git directory paths."""
    try:
        repo_root = call_command(["git", "rev-parse", "--show-toplevel"])
        dot_git_dir = call_command(["git", "rev-parse", "--git-common-dir"])

        abs_repo_root = os.path.abspath(repo_root)
        abs_dot_git_dir = os.path.abspath(dot_git_dir)

        _LOGGER.info("Repository root: %s", abs_repo_root)
        _LOGGER.info(".git directory: %s", abs_dot_git_dir)

        return [abs_repo_root, abs_dot_git_dir]
    except subprocess.CalledProcessError:
        _LOGGER.warning("Not a git repository or git command failed.")
        return []


def collect_write_paths(
    *,
    enable_git: bool,
    enable_cwd: bool,
    enable_awscli: bool,
    enable_cdk: bool,
    write: Sequence[str],
) -> list[str]:
    """Collect all paths that should be writable based on options."""
    paths: list[str] = []

    if enable_git:
        paths.extend(git_subpaths())
    if enable_cwd:
        paths.append(os.getcwd())
    if enable_awscli:
        paths.append(os.path.join(Path.home().as_posix(), ".aws"))
    if enable_cdk:
        paths.append(os.path.join(Path.home().as_posix(), ".cdk"))
    if write:
        paths.extend(write)

    return paths
