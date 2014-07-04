#!/bin/bash

DOT_FILES=(.zsh .zshrc .vimrc .vim)

for file in ${DOT_FILES[@]}
do
	ln -s $HOME/dotfiles/$file $HOME/$file
done

# git config --global core.editor 'vim -c "set fenc=utf-8"'
