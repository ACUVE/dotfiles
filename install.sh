#!/bin/bash

set -xe

# Settings #####
DOT_FILES=(.zsh .zshrc .zshenv .vimrc .vim .easystroke .tmux.conf .env .pep8 .pyenv .digrc)
DOT_DIRECTORY_EACH_FILE=(.ssh .aws)
CONFIG_FILES=(nvim)
################

SCRIPT_DIR=$(cd $(dirname $0); pwd)


# DOT_FILES
for file in ${DOT_FILES[@]}
do
	ln -sfn "${SCRIPT_DIR}/$file" "${HOME}/${file}"
done

# CONFIG_FILES
mkdir -p $HOME/.config
for file in ${CONFIG_FILES[@]}
do
	ln -sfn "${SCRIPT_DIR}/${file}" "${HOME}/.config/${file}"
done

# DOT_DIRECTORY_EACH_FILE
for dir in ${DOT_DIRECTORY_EACH_FILE[@]}
do
    TARGET_DIR="${HOME}/${dir}"
    if [ \! -e "${TARGET_DIR}" ]; then
        mkdir "${TARGET_DIR}"
        # .ssh だけ例外的に 700 である必要性がある
        if [ "${dir}" = ".ssh" ]; then
            chmod 700 "${TARGET_DIR}"
        fi
    fi
    if [ -d "${TARGET_DIR}" ]; then
        for file in "${SCRIPT_DIR}/${dir}"/*; do
            REL_TARGET_PATH="${file#${SCRIPT_DIR}/}"
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

# git config --global core.editor 'vim -c "set fenc=utf-8"'
# go get github.com/nsf/gocode
