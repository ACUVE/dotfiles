#!/bin/bash

DOT_FILES=(.zsh .zshrc .zshenv .vimrc .vim .easystroke .tmux.conf .env .pep8 .pyenv .digrc)
DOT_DIRECTORY_EACH_FILE=(.ssh)
CONFIG_FILES=(nvim)

# DOT_FILES
for file in ${DOT_FILES[@]}
do
	ln -sfn $HOME/dotfiles/$file $HOME/$file
done

# CONFIG_FILES
mkdir -p $HOME/.config
for file in ${CONFIG_FILES[@]}
do
	ln -sfn $HOME/dotfiles/$file $HOME/.config/$file
done

# DOT_DIRECTORY_EACH_FILE
for dir in ${DOT_DIRECTORY_IN_FILE[@]}
do
    TARGET_DIR="$HOME/$dir"
    if [ \! -e "${TARGET_DIR}" ]; then
        mkdir "${TARGET_DIR}"
        # .ssh だけ例外的に 700 である必要性がある
        if [ "${dir}" = ".ssh" ]; then
            chmod 700 "${TARGET_DIR}"
        fi
    fi
    if [ -d "${TARGET_DIR}" ]; then
        for file in "${dir}"/*; do
            ln -sfn $HOME/dotfiles/$file $HOME/$file
        done
    fi
done

# git config --global core.editor 'vim -c "set fenc=utf-8"'
# go get github.com/nsf/gocode
