import os
import sys
from pathlib import Path
from logging import getLogger

_LOGGER = getLogger(__name__)


def sbx(
    write: list[str],
    command: list[str],
) -> None:
    profile = """(version 1)

(allow default)

(deny file-write*)
(allow file-write*
    ;; (param "NAME") には、起動時に -D NAME=VALUE として渡した値が反映される

    ;; プロジェクトディレクトリを TARGET_DIR として指定する
    (subpath (param "TARGET_DIR"))

    ;; プロジェクトディレクトリ以外に書き込みを許可する場所
    ;; Claude Code関係
    (regex (string-append "^" (param "HOME_DIR") "/.claude*"))
    ;; セッション情報をKeychain経由で記録するらしい
    (subpath (string-append (param "HOME_DIR") "/Library/Keychains"))

    ;; 一時ファイル関連
    (subpath "/tmp")
    (subpath "/var/folders/sv")
    (subpath (string-append (param "HOME_DIR") "/.cache"))
    (subpath (string-append (param "HOME_DIR") "/Library/Caches"))

    ;; その他のツール関連。ご利用のツールに合わせて調整してください
    (subpath (string-append (param "HOME_DIR") "/.npm"))

    ;; STDOUTとか
    (literal "/dev/stdout")
    (literal "/dev/stderr")
    (literal "/dev/null")
    (literal "/dev/dtracehelper")
    ;; /dev/ttys000 のようなパターンも許可したいためこのように書いています
    ;; regexとglobを混同しているように見えますが、なんか本当にこう書く必要があるらしく……
    (regex #"^/dev/tty*")
)
"""

    if write:
        additional_dirs = ""
        for directory in write:
            additional_dirs += f'    (subpath "{directory}")\n'
        profile = profile.rstrip("\n)\n") + "\n" + additional_dirs + ")\n"

    home_dir = str(Path.home())
    target_dir = os.getcwd()

    cmd = [
        "sandbox-exec",
        "-p",
        profile,
        "-D",
        f"TARGET_DIR={target_dir}",
        "-D",
        f"HOME_DIR={home_dir}",
    ] + list(command)

    try:
        os.execvp(cmd[0], cmd)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
