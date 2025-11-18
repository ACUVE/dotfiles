#!/bin/bash

set -euxo pipefail

git submodule update --init --recursive || true

# Settings #####
DOT_FILES=(.zsh .zshrc .zshenv .vimrc .vim .easystroke .tmux.conf .shenv .pep8 .pyenv .digrc .bin .bashrc .sh_profile .bash_profile)
DOT_DIRECTORY_EACH_FILE=(.ssh .aws .awsume)
CONFIG_FILES=(nvim git mise pnpm)
OLD_DOT_FILES=(.env)  # 過去管理していたが、現在は管理していないファイル群
OLD_CONFIG_FILES=(claude)  # 過去管理していたが、現在は管理していないファイル群
################

SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)


# DOT_FILES
for file in "${DOT_FILES[@]}"
do
	ln -sfn "${SCRIPT_DIR}/root/${file#.}" "${HOME}/${file}"
done
# OLD_DOT_FILES
for file in "${OLD_DOT_FILES[@]}"
do
    if [ -L "${HOME}/${file}" ] && [ ! -e "${HOME}/${file}" ]; then
        rm "${HOME}/${file}"
    fi
done

# CONFIG_FILES
mkdir -p "$HOME/.config"
for file in "${CONFIG_FILES[@]}"
do
	ln -sfn "${SCRIPT_DIR}/config/${file}" "${HOME}/.config/${file}"
done
# OLD_CONFIG_FILES
for file in "${OLD_CONFIG_FILES[@]}"
do
    if [ -L "${HOME}/.config/${file}" ] && [ ! -e "${HOME}/.config/${file}" ]; then
        rm "${HOME}/.config/${file}"
    fi
done

# DOT_DIRECTORY_EACH_FILE
for dir in "${DOT_DIRECTORY_EACH_FILE[@]}"
do
    TARGET_DIR="${HOME}/${dir}"
    if [ ! -e "${TARGET_DIR}" ]; then
        mkdir "${TARGET_DIR}"
        # .ssh だけ例外的に 700 である必要性がある
        if [ "${dir}" = ".ssh" ]; then
            chmod 700 "${TARGET_DIR}"
        fi
    fi
    if [ -d "${TARGET_DIR}" ]; then
        for file in "${SCRIPT_DIR}/${dir}"/*; do
            REL_TARGET_PATH="${file#"${SCRIPT_DIR}"/}"
            ln -sfn "${file}" "${HOME}/${REL_TARGET_PATH}"
            # .ssh だけ 600 である必要性がある
            if [ "${dir}" = ".ssh" ]; then
                if [ -d "${HOME}/${REL_TARGET_PATH}" ]; then
                    chmod 700 "${HOME}/${REL_TARGET_PATH}"
                else
                    chmod 600 "${HOME}/${REL_TARGET_PATH}"
                fi
            fi
        done
    fi
done

# Claude Code が XDG の仕様に沿ってないので、仕方なく一部分離
ln -sfn "${SCRIPT_DIR}/claude_agents" "${CLAUDE_CONFIG_DIR:-"${HOME}/.claude"}/agents"


# git config --global core.editor 'vim -c "set fenc=utf-8"'
# go get github.com/nsf/gocode
