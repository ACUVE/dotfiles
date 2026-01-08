"""macOS sandbox implementation using sandbox-exec."""

import os
import shlex
import sys
from logging import getLogger
from pathlib import Path
from typing import Literal, LiteralString, Sequence

from .ast import ASTNode, SExpression, String, Symbol
from .parser import parse
from .._common import collect_write_paths

_LOGGER = getLogger(__name__)


def default_profile() -> list[ASTNode]:
    """Build the sandbox profile."""
    profile = """(version 1)

(allow default)

(import "system.sb")

(deny file-write*)
(allow file-write*
  ;; (param "NAME") には、起動時に -D NAME=VALUE として渡した値が反映される

  ;; プロジェクトディレクトリ以外に書き込みを許可する場所
  ;; セッション情報をKeychain経由で記録するらしい
  (subpath (string-append (param "HOME_DIR") "/Library/Keychains"))

  ;; 一時ファイル関連
  (subpath "/private/tmp")
  (subpath "/private/var/tmp")
  (subpath "/private/var/folders")
  (subpath (string-append (param "HOME_DIR") "/.cache"))
  (subpath (string-append (param "HOME_DIR") "/Library/Caches"))
  (subpath (string-append (param "HOME_DIR") "/.local/share"))
  (regex (string-append "^" (regex-quote (param "HOME_DIR")) "/.ssh/.mux-*"))

  (subpath (string-append (param "HOME_DIR") "/.npm"))
  (subpath (string-append (param "HOME_DIR") "/.pnpm"))

  ;; STDOUTとか
  (literal "/dev/stdout")
  (literal "/dev/stderr")
  (literal "/dev/null")
  (literal "/dev/ptmx")
  (literal "/dev/dtracehelper")
  ;; /dev/ttys000 のようなパターンも許可したいためこのように書いています
  ;; regexとglobを混同しているように見えますが、なんか本当にこう書く必要があるらしく……
  (regex #"^/dev/tty*")
)

;; --- 禁止: node_modules とロックファイルへの書き込みを全域で拒否 ---
(deny file-write*
  ;; どのディレクトリ配下でも node_modules/ そのもの/配下を拒否
  ;; (regex #".*/node_modules(/|$)")
  ;; (regex #".*/.venv(/|$)")

  ;; ロックファイル（場所を問わずファイル名で拒否）
  ;; (regex #".*/package-lock\\.json$")
  ;; (regex #".*/pnpm-lock\\.yaml$")
  ;; (regex #".*/yarn\\.lock$")
  ;; (regex #".*/uv\\.lock$")
  ;; (regex #".*/poetry\\.lock$")

  ;; .env
  (regex #".*/\\.env$")
  ;; (regex #".*/\\.env\\..*$")
)

(allow file-write*
  ;; vitestが使うので許可
  (regex #".*/node_modules/\\.vite-temp(/|$)")
)

;; --- 機密ファイルの"内容読み取り"を禁止 (statは可) ---
(deny file-read-data
  (literal (string-append (param "HOME_DIR") "/.aws/credentials"))
  (literal (string-append (param "HOME_DIR") "/.zsh_history"))
  (literal (string-append (param "HOME_DIR") "/.bash_history"))
)

;; Keychain 解錠や設定参照など
(allow mach-lookup
  (global-name "com.apple.securityd")
  (global-name "com.apple.cfprefsd.xpc.agent")
  (global-name "com.apple.cfprefsd.xpc.daemon")
  (global-name "com.apple.ocspd")
  (global-name "com.apple.notifyd")
  (global-name "com.apple.SystemConfiguration.DNSConfiguration")
  (global-name "com.apple.coreservices.launchservicesd")
)

(allow ipc-posix-shm*
  (ipc-posix-name "com.apple.AppleDatabaseChanged")
)
"""
    return parse(profile)


def _get_or_insert_allow_deny(
    profile_nodes: list[ASTNode],
    action: Literal["allow", "deny"],
    operation: LiteralString,
) -> SExpression:
    """Get or insert an allow/deny expression for the given operation."""
    for node in profile_nodes:
        if (
            isinstance(node, SExpression)
            and len(node.elements) > 0
            and isinstance(node.elements[0], Symbol)
            and node.elements[0].name == action
            and len(node.elements) > 1
            and isinstance(node.elements[1], Symbol)
            and node.elements[1].name == operation
        ):
            return node

    # Not found, create a new one
    new_node = SExpression([Symbol(action), Symbol(operation)])
    profile_nodes.append(new_node)
    return new_node


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
    """Execute a command in a sandboxed environment using sandbox-exec."""
    profile = default_profile()

    additional_allow_write_subpaths = collect_write_paths(
        enable_git=enable_git,
        enable_cwd=enable_cwd,
        enable_awscli=enable_awscli,
        enable_cdk=enable_cdk,
        write=write,
    )

    if additional_allow_write_subpaths:
        allow_file_write = _get_or_insert_allow_deny(profile, "allow", "file-write*")
        for path in additional_allow_write_subpaths:
            allow_file_write.elements.append(
                SExpression([Symbol("subpath"), String(path)])
            )

    profile_str = "\n\n".join(node.to_string() for node in profile)

    _LOGGER.info("Using sandbox profile:\n%s", profile_str)

    cmd = [
        "sandbox-exec",
        "-p",
        profile_str,
        "-D",
        f"HOME_DIR={Path.home().as_posix()}",
        "--",
    ] + list(command)

    try:
        if dry_run:
            print(" ".join(shlex.quote(arg) for arg in cmd))
        else:
            os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
