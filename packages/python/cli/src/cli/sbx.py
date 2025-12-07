import os
import shlex
import subprocess
import sys
from logging import DEBUG, getLogger
from pathlib import Path
from typing import Sequence

from cli.sbx_ast import Integer, Regex, SExpression, String, Symbol

_LOGGER = getLogger(__name__)


def _build_profile() -> list[SExpression]:
    """Build the sandbox profile as AST nodes."""
    return [
        # (version 1)
        SExpression([Symbol("version"), Integer(1)]),
        # (allow default)
        SExpression([Symbol("allow"), Symbol("default")]),
        # (import "system.sb")
        SExpression([Symbol("import"), String("system.sb")]),
        # (deny file-write*)
        SExpression([Symbol("deny"), Symbol("file-write*")]),
        # (allow file-write* ...)
        SExpression(
            [
                Symbol("allow"),
                Symbol("file-write*"),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression([Symbol("param"), String("TARGET_DIR")]),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression([Symbol("param"), String("DOT_GIT_DIR")]),
                    ]
                ),
                SExpression(
                    [
                        Symbol("regex"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                String("^"),
                                SExpression(
                                    [Symbol("param"), String("CLAUDE_CONFIG_DIR")]
                                ),
                                String("*"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("regex"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                String("^"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.claude*"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/Library/Keychains"),
                            ]
                        ),
                    ]
                ),
                SExpression([Symbol("subpath"), String("/private/tmp")]),
                SExpression([Symbol("subpath"), String("/private/var/tmp")]),
                SExpression([Symbol("subpath"), String("/private/var/folders")]),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.cache"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/Library/Caches"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.local/share"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.npm"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.pnpm"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.yarn"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.serena"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("subpath"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.codex"),
                            ]
                        ),
                    ]
                ),
                SExpression([Symbol("literal"), String("/dev/stdout")]),
                SExpression([Symbol("literal"), String("/dev/stderr")]),
                SExpression([Symbol("literal"), String("/dev/null")]),
                SExpression([Symbol("literal"), String("/dev/ptmx")]),
                SExpression([Symbol("literal"), String("/dev/dtracehelper")]),
                SExpression([Symbol("regex"), Regex("^/dev/tty*")]),
            ]
        ),
        # (deny file-write* ...)
        SExpression(
            [
                Symbol("deny"),
                Symbol("file-write*"),
                SExpression([Symbol("regex"), Regex(".*/\\.env$")]),
            ]
        ),
        # (allow file-write* ...)
        SExpression(
            [
                Symbol("allow"),
                Symbol("file-write*"),
                SExpression(
                    [Symbol("regex"), Regex(".*/node_modules/\\.vite-temp(/|$)")]
                ),
            ]
        ),
        # (deny file-read-data ...)
        SExpression(
            [
                Symbol("deny"),
                Symbol("file-read-data"),
                SExpression(
                    [
                        Symbol("literal"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.aws/credentials"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("literal"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.zsh_history"),
                            ]
                        ),
                    ]
                ),
                SExpression(
                    [
                        Symbol("literal"),
                        SExpression(
                            [
                                Symbol("string-append"),
                                SExpression([Symbol("param"), String("HOME_DIR")]),
                                String("/.bash_history"),
                            ]
                        ),
                    ]
                ),
            ]
        ),
        # (allow mach-lookup ...)
        SExpression(
            [
                Symbol("allow"),
                Symbol("mach-lookup"),
                SExpression([Symbol("global-name"), String("com.apple.securityd")]),
                SExpression(
                    [Symbol("global-name"), String("com.apple.cfprefsd.xpc.agent")]
                ),
                SExpression(
                    [Symbol("global-name"), String("com.apple.cfprefsd.xpc.daemon")]
                ),
                SExpression([Symbol("global-name"), String("com.apple.ocspd")]),
                SExpression([Symbol("global-name"), String("com.apple.notifyd")]),
                SExpression(
                    [
                        Symbol("global-name"),
                        String("com.apple.SystemConfiguration.DNSConfiguration"),
                    ]
                ),
                SExpression(
                    [
                        Symbol("global-name"),
                        String("com.apple.coreservices.launchservicesd"),
                    ]
                ),
            ]
        ),
        # (allow ipc-posix-shm* ...)
        SExpression(
            [
                Symbol("allow"),
                Symbol("ipc-posix-shm*"),
                SExpression(
                    [Symbol("ipc-posix-name"), String("com.apple.AppleDatabaseChanged")]
                ),
            ]
        ),
    ]


def sbx(
    write: Sequence[str],
    command: Sequence[str],
) -> None:
    repo_root = _call_command(["git", "rev-parse", "--show-toplevel"])
    dot_git_dir = _call_command(["git", "rev-parse", "--git-common-dir"])
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))

    _LOGGER.info("Repository root: %s", repo_root)
    _LOGGER.info(".git directory: %s", dot_git_dir)

    # Build profile from AST nodes
    profile_nodes = _build_profile()
    profile = "\n\n".join(node.to_string() for node in profile_nodes)

    if write:
        _LOGGER.error("Specifying additional write directories is not supported yet.")
        sys.exit(1)

    home_dir = str(Path.home())
    target_dir = os.getcwd()

    cmd = [
        "sandbox-exec",
        "-p",
        profile,
        "-D",
        f"TARGET_DIR={target_dir}",
        "-D",
        f"DOT_GIT_DIR={dot_git_dir}",
        "-D",
        f"CLAUDE_CONFIG_DIR={claude_dir}",
        "-D",
        f"HOME_DIR={home_dir}",
    ] + list(command)

    try:
        os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _call_command(cmd: Sequence[str]) -> str:
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
