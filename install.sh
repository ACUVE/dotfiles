#!/bin/bash

DOT_FILES=(.zsh .zshrc .zshenv .vimrc .vim .easystroke .tmux.conf)
CONFIG_FILES=(nvim)

for file in ${DOT_FILES[@]}
do
	ln -sfn $HOME/dotfiles/$file $HOME/$file
done
for file in ${CONFIG_FILES[@]}
do
	ln -sfn $HOME/dotfiles/$file $HOME/.config/$file
done

# git config --global core.editor 'vim -c "set fenc=utf-8"'
# go get github.com/nsf/gocode
