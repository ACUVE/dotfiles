#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
使い方: install.sh [オプション]

  -n, --dry-run   実際には何も変更せず、何が行われるかだけを表示する
  -h, --help      このヘルプを表示する

環境変数:
  DOTFILES_NO_WINDOWS_ENV=1   Windows ユーザー環境変数の設定をスキップする
EOF
}

DRY_RUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        *)            printf >&2 'install.sh: 不明なオプション: %s\n\n' "$1"; usage; exit 1 ;;
    esac
done

# ============================================================
#  プラットフォーム判定
#
#  OS 判定は「管理対象の取捨選択」ではなく「振る舞いの分岐」にのみ使う。
#  管理対象リスト（DOT_FILES 等）は全プラットフォームで同一に保つこと。
#  Windows で使えないもの（zsh 設定・tmux.conf・Brewfile 等）も、
#  リンクしておけば後からツールを入れた時点で自動的に効く。
#
#  ※ $OSTYPE は使わないこと。Git Bash (MINGW64) は 'cygwin' を返すため、
#     よくある `case "$OSTYPE" in msys*)` は黙ってすり抜ける。
# ============================================================
detect_os() {
    case "$(uname -s)" in
        Darwin*)              printf 'macos'   ;;
        Linux*)               printf 'linux'   ;;  # WSL もここに含まれる
        MINGW*|MSYS*|CYGWIN*) printf 'windows' ;;
        *)                    printf 'unknown' ;;
    esac
}
OS="$(detect_os)"

info() { printf '%s\n' "$*"; }
warn() { printf >&2 'install.sh: warning: %s\n' "$*"; }
die()  { printf >&2 'install.sh: error: %s\n' "$*"; exit 1; }

# $HOME 配下のパスを ~ 表記に短縮する（出力を読みやすくするためだけのもの）
tilde() {
    case "$1" in
        "$HOME"/*) printf '~%s' "${1#"$HOME"}" ;;
        *)         printf '%s' "$1" ;;
    esac
}

# 「何を」「どうする」かを揃えて出力する
#   report <動作> <対象> [補足]
report() { printf '  %-10s %s%s\n' "$1" "$2" "${3:+  # $3}"; }

# dry-run 中は実行せず、実行時のみコマンドを走らせる
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        return 0
    fi
    "$@"
}

SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)

# Settings #####
DOT_FILES=(.zsh .zshrc .zshenv .vimrc .vim .easystroke .tmux.conf .shenv .sh_os .pep8 .digrc .bin .bashrc .sh_profile .bash_profile .zprofile Brewfile)
DOT_DIRECTORY_EACH_FILE=(.ssh .aws .awsume)
CONFIG_FILES=(nvim git mise pnpm npm docker uv claude powershell)
CONFIG_FILES_SINGLE_FILE=(jj/config.toml)
# OS ごとに配置先が異なるものの追加リンク
#   "<repo 内の相対パス> <$HOME からの相対パス>"
# PowerShell のプロファイル位置:
#   macOS/Linux : ~/.config/powershell/  （CONFIG_FILES の powershell でカバー済み）
#   Windows     : ~/Documents/PowerShell/
# ディレクトリごとではなく profile.ps1 単体をリンクする。
# Install-Module -Scope CurrentUser が Documents/PowerShell/Modules に書くため、
# ディレクトリをリンクすると repo にモジュールが降ってくる。
WINDOWS_EXTRA_LINKS=(
    "config/powershell/profile.ps1 Documents/PowerShell/profile.ps1"
)
OLD_DOT_FILES=(.env .gitignore .pyenv)  # 過去管理していたが、現在は管理していないファイル群
OLD_CONFIG_FILES=()  # 過去管理していたが、現在は管理していないファイル群
# OLD_CONFIG_FILES_SINGLE_FILE=()  # 過去管理していたが、現在は管理していないファイル群（コメントアウトしているのは、空のため）
################

SYMLINK_HELP='ネイティブ NTFS シンボリックリンクを作成できません。

  Windows の開発者モードを有効にしてください（マシンごとに一度だけ必要）:
    設定 > システム > 開発者向け > 開発者モード = オン
  その後、Git Bash をすべて閉じて開き直し、./install.sh を再実行してください。

  ※ 確認は `whoami /priv` で行わないでください。開発者モードは
     SeCreateSymbolicLinkPrivilege を付与しないため、成功していても
     この特権は現れません。`ln -s` が通るかで判断してください。

  （代替: Git Bash を管理者として実行する、または secpol.msc の
   ローカルポリシー > ユーザー権利の割り当て >「シンボリック リンクの作成」
   に自分のアカウントを追加する）'


# ------------------------------------------------------------
#  Windows プリフライト
# ------------------------------------------------------------
windows_preflight() {
    # MSYS は msys-2.0.dll が子プロセス起動時に読むため、
    # ここで export すれば以降の ln に効く（再 exec は不要）。
    # これを設定しないと ln -s は「無警告でコピーを作り exit 0 を返す」ため、
    # 一見成功したように見えて repo と切り離された実体ができてしまう。
    case "${MSYS:-}" in
        *winsymlinks:nativestrict*) : ;;
        *) export MSYS="${MSYS:+${MSYS} }winsymlinks:nativestrict" ;;
    esac

    # 実際に symlink を作れるか事前検証し、失敗するなら 1 度だけ明確に落とす。
    # （個々の ln が延々と失敗するより、先に 1 回で止めた方が分かりやすい）
    # コピーモードでは通常ファイルになるため [ -L ] で確実に見分けられる。
    # dry-run でも「本番実行が通るか」を知りたいので、この検証だけは常に行う。
    local probe rc
    probe="${HOME}/.dotfiles-symlink-probe.$$"
    rm -rf "$probe" 2>/dev/null || true
    mkdir -p "$probe" || die "検証用ディレクトリを作成できません: ${probe}"
    : > "${probe}/target"
    rc=1
    if ln -s "${probe}/target" "${probe}/link" 2>/dev/null && [ -L "${probe}/link" ]; then
        rc=0
    fi
    rm -rf "$probe" 2>/dev/null || true
    if [ "$rc" -ne 0 ]; then
        die "$SYMLINK_HELP"
    fi
    info "ネイティブシンボリックリンク: 利用可能"
}


# ------------------------------------------------------------
#  リポジトリ内のコミット済み symlink を実体化する
#
#  core.symlinks=false のまま clone すると、git は mode 120000 のブロブを
#  「リンク先パスを内容とする通常ファイル」として書き出す。
#  インデックスの mode は 120000 のままで stat 情報も記録されるため、
#  git status はクリーンと判定し、checkout / restore / reset --hard は
#  いずれも該当パスをスキップする。よって削除してから checkout し直す。
# ------------------------------------------------------------
git_fix_symlinks() {
    local repo="$1" label="$2"
    local paths=() p

    [ -e "${repo}/.git" ] || return 0

    if [ "$(git -C "$repo" config --get core.symlinks 2>/dev/null || true)" != "true" ]; then
        report "config" "${label}" "core.symlinks=true を設定"
        run git -C "$repo" config core.symlinks true
    fi

    while IFS= read -r p; do
        [ -n "$p" ] || continue
        if [ -e "${repo}/${p}" ] && [ ! -L "${repo}/${p}" ]; then
            paths+=("$p")
        fi
    done <<EOF
$(git -C "$repo" ls-files -s | awk -F'\t' '$1 ~ /^120000 / { print $2 }')
EOF

    [ "${#paths[@]}" -gt 0 ] || return 0

    report "restore" "${label}" "symlink ${#paths[@]} 件を再展開"
    for p in "${paths[@]}"; do
        report "" "  ${p}"
        run rm -f "${repo}/${p}"
    done
    run git -C "$repo" checkout -- "${paths[@]}"
}

git_fix_symlinks_all() {
    local sm
    git_fix_symlinks "$SCRIPT_DIR" "."
    while IFS= read -r sm; do
        [ -n "$sm" ] || continue
        git_fix_symlinks "${SCRIPT_DIR}/${sm}" "$sm"
    done <<EOF
$(git -C "$SCRIPT_DIR" submodule --quiet foreach --recursive 'printf "%s\n" "$displaypath"' 2>/dev/null || true)
EOF
}


# ------------------------------------------------------------
#  リンク作成
# ------------------------------------------------------------
link() {
    local src="$1" dst="$2" bak

    # ln -sfn は dst が実ディレクトリの場合、置き換えずに「中に」リンクを作る。
    # ~/.claude や ~/.config のような実ディレクトリを壊さないよう明示的に拒否する。
    if [ -d "$dst" ] && [ ! -L "$dst" ]; then
        report "SKIP" "$(tilde "$dst")" "実ディレクトリのためネストさせない"
        return 0
    fi

    if [ -L "$dst" ]; then
        if [ "$(readlink "$dst")" = "$src" ]; then
            report "ok" "$(tilde "$dst")"
            return 0
        fi
        report "relink" "$(tilde "$dst")" "現在: $(readlink "$dst")"
    elif [ -e "$dst" ]; then
        # 既存の実ファイルは退避してから置き換える
        bak="${dst}.dotfiles-backup"
        if [ -e "$bak" ]; then
            report "SKIP" "$(tilde "$dst")" "退避先 ${bak##*/} が既に存在"
            return 0
        fi
        report "backup" "$(tilde "$dst")" "-> ${bak##*/} に退避してからリンク"
        run mv "$dst" "$bak"
    else
        report "create" "$(tilde "$dst")"
    fi

    run mkdir -p "$(dirname "$dst")"
    # symlink 作成の失敗は warn に留める。systemic な失敗は
    # windows_preflight が先に検出しているため、ここでの単発失敗で全体を止めない。
    if [ "$DRY_RUN" -eq 0 ]; then
        if ! ln -sfn "$src" "$dst"; then
            warn "symlink の作成に失敗: '${dst}' -> '${src}'"
        fi
    fi
}

# .ssh のパーミッション設定
#
#  Windows(MSYS) では /etc/fstab が noacl でマウントするため chmod は
#  NTFS に対して完全な no-op。NTFS 側はユーザープロファイルからの継承で
#  既に適切な ACL（SYSTEM / Administrators / 本人のみ）を持っているため
#  何もしなくてよい。
#  また chmod は symlink を辿るため、リンクには適用しない
#  （適用するとリンク先＝repo 内のファイルを変更してしまう）。
ssh_harden() {
    if [ "$OS" = "windows" ]; then
        return 0
    fi
    if [ -L "$1" ]; then
        return 0
    elif [ -d "$1" ]; then
        run chmod 700 "$1"
    elif [ -e "$1" ]; then
        run chmod 600 "$1"
    fi
}


# ------------------------------------------------------------
#  Windows ユーザー環境変数
#
#  root/sh_profile は bash_profile/zprofile 経由、つまりログインシェルでしか
#  読まれない。PowerShell やスタートメニューから起動したネイティブ Windows
#  プロセス、および非ログインの bash はこれらの env var を一切見ない。
#  そのままだと「Git Bash の claude は ~/.config/claude、PowerShell の claude は
#  ~/.claude を見る」という分裂状態を install.sh 自身が作り出してしまう。
#
#  ※ 値の定義は root/sh_profile と対になっている。片方だけ変更しないこと。
# ------------------------------------------------------------
WINDOWS_USER_ENV=(
    "XDG_CONFIG_HOME .config"
    "NPM_CONFIG_USERCONFIG .config/npm/npmrc"
    "CLAUDE_CONFIG_DIR .config/claude"
    # DOCKER_CONFIG は意図的に見送り。
    # config/docker/config.json が /opt/homebrew のパスと、Windows に存在しない
    # bw-docker credential helper を参照しているため、壊れた設定を渡すより
    # 未設定のままの方が安全。config を OS 中立化してから追加すること。
)

# HKCU\Environment から現在値を読む。未設定なら空文字。
# MSYS_NO_PATHCONV=1 が無いと '/v' が 'C:/Program Files/Git/v' に変換されて reg が失敗する。
# 値が未設定のとき reg query は exit 1 を返す。set -o pipefail 下では
# パイプライン全体が失敗扱いになり set -e で異常終了するため || true で吸収する。
win_user_env_get() {
    { MSYS_NO_PATHCONV=1 reg query 'HKCU\Environment' /v "$1" 2>/dev/null || true; } \
        | sed -n "s/^[[:space:]]*$1[[:space:]]\{1,\}REG_[A-Z_]\{1,\}[[:space:]]\{1,\}//p" \
        | tr -d '\r'
}

windows_persist_env() {
    local rec name relpath value current changed=0
    info "Windows ユーザー環境変数 (HKCU\\Environment):"
    for rec in "${WINDOWS_USER_ENV[@]}"; do
        # レコードを空白で分割する意図的な単語分割
        # shellcheck disable=SC2086
        set -- $rec
        name="$1"
        relpath="$2"
        value="$(cygpath -w "${HOME}/${relpath}")"
        current="$(win_user_env_get "$name")"
        if [ "$current" = "$value" ]; then
            report "ok" "${name}=${value}"
        else
            report "set" "${name}=${value}" "旧: ${current:-未設定}"
            run setx "$name" "$value" >/dev/null
            run export "${name}=${value}"
            changed=1
        fi
    done
    if [ "$changed" -eq 1 ]; then
        info "  ※ setx は新規プロセスにのみ反映されます。端末や VS Code の再起動が必要です。"
    fi
}


# ------------------------------------------------------------
#  ~/.claude を CLAUDE_CONFIG_DIR (~/.config/claude) へ移行する
#
#  macOS では sh_profile が CLAUDE_CONFIG_DIR=~/.config/claude を export
#  しているため、実行時状態は元から repo 配下に置かれる。Windows でも
#  同じ構成に揃えるため、既存の ~/.claude の中身を移動する。
#  コピーではなく move なのは、数百 MB 規模になり得るため。
# ------------------------------------------------------------
claude_is_running() {
    powershell.exe -NoProfile -Command \
        'if (Get-Process claude -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }' \
        >/dev/null 2>&1
}

migrate_claude_config_dir() {
    local legacy="${HOME}/.claude"
    local target="${HOME}/.config/claude"
    local entry base moved=0

    if [ ! -d "$legacy" ] || [ -L "$legacy" ]; then
        return 0
    fi
    # dry-run 中は target がまだ無いこともあるので、その場合は予告だけする
    if [ ! -d "$target" ] && [ "$DRY_RUN" -eq 0 ]; then
        return 0
    fi

    # 稼働中に移動するとファイルハンドルを掴まれていて失敗するか、
    # セッション状態を壊しかねない。
    if claude_is_running; then
        warn "Claude Code が稼働中のため ~/.claude の移行をスキップしました。
  Claude Code を終了してから ./install.sh を再実行してください。"
        return 0
    fi

    for entry in "${legacy}"/* "${legacy}"/.[!.]*; do
        if [ ! -e "$entry" ] && [ ! -L "$entry" ]; then
            continue
        fi
        base="$(basename "$entry")"
        # dotfiles が管理しているものは移行しない（repo 側が正）
        case "$base" in
            settings.json|mcp.json|.gitignore|agents|skills) continue ;;
        esac
        # 移行先に既にあるものは触らない
        if [ -e "${target}/${base}" ]; then
            continue
        fi
        if [ "$moved" -eq 0 ]; then
            info "~/.claude を $(tilde "$target") へ移行:"
        fi
        report "move" "${base}"
        run mv "$entry" "${target}/${base}"
        moved=1
    done

    if [ "$moved" -eq 1 ]; then
        info "  ~/.claude は残しています（settings.json 等のマシン固有設定を確認後、手動で削除してください）"
    fi
}


# ============================================================
#  main
# ============================================================
if [ "$OS" = "unknown" ]; then
    die "未対応のプラットフォームです: $(uname -s)"
fi

if [ "$DRY_RUN" -eq 1 ]; then
    info "*** DRY-RUN: 実際には何も変更しません ***"
fi
info "platform: ${OS}"
info ""

if [ "$OS" = "windows" ]; then
    windows_preflight
fi

info "submodule:"
if [ "$DRY_RUN" -eq 1 ]; then
    report "skip" "git submodule update --init --recursive" "dry-run のため実行しない"
elif ! git -C "$SCRIPT_DIR" submodule update --init --recursive; then
    warn "サブモジュールの更新に失敗しました。private_config を参照するリンク（.ssh / .aws）が壊れる可能性があります"
fi

# サブモジュールの展開後に実行すること。
# NTFS の symlink はファイル型/ディレクトリ型が作成時に確定して後から直せないため、
# .ssh/conf.d -> ../private_config/ssh/conf.d のリンク先が実在している必要がある。
info "repo 内の symlink:"
git_fix_symlinks_all

# DOT_FILES
info ""
info "DOT_FILES (~/):"
for file in "${DOT_FILES[@]}"
do
    link "${SCRIPT_DIR}/root/${file#.}" "${HOME}/${file}"
done
# OLD_DOT_FILES
for file in "${OLD_DOT_FILES[@]}"
do
    if [ -L "${HOME}/${file}" ] && [ ! -e "${HOME}/${file}" ]; then
        report "remove" "~/${file}" "リンク切れの旧管理ファイル"
        run rm "${HOME}/${file}"
    fi
done

# CONFIG_FILES
info ""
info "CONFIG_FILES (~/.config/):"
run mkdir -p "$HOME/.config"
for file in "${CONFIG_FILES[@]}"
do
    link "${SCRIPT_DIR}/config/${file}" "${HOME}/.config/${file}"
done
# CONFIG_FILES_SINGLE_FILE
for file in "${CONFIG_FILES_SINGLE_FILE[@]}"
do
    link "${SCRIPT_DIR}/config/${file}" "${HOME}/.config/${file}"
done
# OLD_CONFIG_FILES
for file in ${OLD_CONFIG_FILES[@]+"${OLD_CONFIG_FILES[@]}"}
do
    if [ -L "${HOME}/.config/${file}" ] && [ ! -e "${HOME}/.config/${file}" ]; then
        report "remove" "~/.config/${file}" "リンク切れの旧管理ファイル"
        run rm "${HOME}/.config/${file}"
    fi
done
# OLD_CONFIG_FILES_SINGLE_FILE
# for file in "${OLD_CONFIG_FILES_SINGLE_FILE[@]}"
# do
#     if [ -L "${HOME}/.config/${file}" ] && [ ! -e "${HOME}/.config/${file}" ]; then
#         rm "${HOME}/.config/${file}"
#     fi
# done

# DOT_DIRECTORY_EACH_FILE
info ""
info "DOT_DIRECTORY_EACH_FILE:"
for dir in "${DOT_DIRECTORY_EACH_FILE[@]}"
do
    TARGET_DIR="${HOME}/${dir}"
    if [ ! -e "${TARGET_DIR}" ]; then
        report "mkdir" "~/${dir}"
        run mkdir "${TARGET_DIR}"
    fi
    # .ssh だけ例外的に 700/600 である必要性がある
    if [ "${dir}" = ".ssh" ]; then
        ssh_harden "${TARGET_DIR}"
    fi
    if [ -d "${TARGET_DIR}" ] || [ "$DRY_RUN" -eq 1 ]; then
        for file in "${SCRIPT_DIR}/${dir}"/*; do
            # -L も見るのは、.aws/credentials が secrets unlock 前は
            # リンク切れ（-e が false）になるため。
            # ディレクトリが空の場合に glob がリテラルの '*' に化けるのも防ぐ。
            if [ ! -e "$file" ] && [ ! -L "$file" ]; then
                continue
            fi
            REL_TARGET_PATH="${file#"${SCRIPT_DIR}"/}"
            link "${file}" "${HOME}/${REL_TARGET_PATH}"
            if [ "${dir}" = ".ssh" ]; then
                ssh_harden "${HOME}/${REL_TARGET_PATH}"
            fi
        done
    fi
done

if [ "$OS" = "windows" ]; then
    info ""
    info "Windows 固有の配置先:"
    for rec in "${WINDOWS_EXTRA_LINKS[@]}"; do
        # レコードを空白で分割する意図的な単語分割
        # shellcheck disable=SC2086
        set -- $rec
        link "${SCRIPT_DIR}/$1" "${HOME}/$2"
    done

    info ""
    if [ -z "${DOTFILES_NO_WINDOWS_ENV:-}" ]; then
        windows_persist_env
    fi
    migrate_claude_config_dir
    info ""
    info "note: Windows では .ssh の chmod をスキップしました（MSYS は NTFS を noacl でマウントするため no-op）"
fi

# Homebrew Bundle
if command -v brew >/dev/null 2>&1; then
    info ""
    info "Homebrew Bundle:"
    if [ "$DRY_RUN" -eq 1 ]; then
        report "skip" "brew bundle" "dry-run のため実行しない"
    else
        # pushd/popd は set -e 下で pushd が失敗すると popd が誤動作するためサブシェルにする
        ( cd "${HOME}" && HOMEBREW_BUNDLE_NO_UPGRADE="1" brew bundle )
    fi
fi

info ""
if [ "$DRY_RUN" -eq 1 ]; then
    info "*** DRY-RUN 終了: 実際には何も変更していません ***"
else
    info "完了しました。"
fi
