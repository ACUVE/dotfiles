#!/bin/bash

DOT_FILES=(.zsh .zshrc .vimrc .vim .easystroke)

for file in ${DOT_FILES[@]}
do
	ln -sfn $HOME/dotfiles/$file $HOME/$file
done

# git config --global core.editor 'vim -c "set fenc=utf-8"'
