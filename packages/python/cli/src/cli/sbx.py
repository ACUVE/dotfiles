import os
import shlex
import subprocess
import sys
from logging import DEBUG, getLogger
from pathlib import Path
from typing import Sequence

_LOGGER = getLogger(__name__)


def default_profile() -> str:
    """Build the sandbox profile."""
    return """(version 1)

(allow default)

(import "system.sb")

(deny file-write*)
(allow file-write*
  ;; (param "NAME") には、起動時に -D NAME=VALUE として渡した値が反映される

  ;; プロジェクトディレクトリを TARGET_DIR として指定する
  (subpath (param "TARGET_DIR"))

  ;; git worktree を使っている場合に、御本尊の .git への書き込みを許可する (commit などできるように)
  (subpath (param "DOT_GIT_DIR"))

  ;; プロジェクトディレクトリ以外に書き込みを許可する場所
  ;; Claude Code関係
  (regex (string-append "^" (param "CLAUDE_CONFIG_DIR") "*"))
  (regex (string-append "^" (param "HOME_DIR") "/.claude*"))
  ;; セッション情報をKeychain経由で記録するらしい
  (subpath (string-append (param "HOME_DIR") "/Library/Keychains"))

  ;; 一時ファイル関連
  (subpath "/private/tmp")
  (subpath "/private/var/tmp")
  (subpath "/private/var/folders")
  (subpath (string-append (param "HOME_DIR") "/.cache"))
  (subpath (string-append (param "HOME_DIR") "/Library/Caches"))
  (subpath (string-append (param "HOME_DIR") "/.local/share"))

  (subpath (string-append (param "HOME_DIR") "/.npm"))
  (subpath (string-append (param "HOME_DIR") "/.pnpm"))
  (subpath (string-append (param "HOME_DIR") "/.yarn"))
  (subpath (string-append (param "HOME_DIR") "/.serena"))

  (subpath (string-append (param "HOME_DIR") "/.codex"))

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


def sbx(
    *,
    write: Sequence[str],
    command: Sequence[str],
) -> None:
    repo_root = _call_command(["git", "rev-parse", "--show-toplevel"])
    dot_git_dir = _call_command(["git", "rev-parse", "--git-common-dir"])
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))

    _LOGGER.info("Repository root: %s", repo_root)
    _LOGGER.info(".git directory: %s", dot_git_dir)

    profile = default_profile()

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
