# The following lines were added by compinstall

zstyle ':completion:*' expand prefix suffix
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-suffixes true
zstyle ':completion:*' original true
zstyle ':completion:*' squeeze-slashes true
zstyle :compinstall filename '/home/acuve/.zshrc'

autoload -Uz compinit
compinit
# End of lines added by compinstall
# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
# End of lines configured by zsh-newuser-install

zstyle ':completion:*' ignore-parents parent pwd ..
setopt auto_cd
setopt auto_list
setopt hist_ignore_space
setopt hist_ignore_all_dups
disable r

bindkey -e
bindkey "^?"    backward-delete-char
bindkey "^H"    backward-delete-char
bindkey "^[[3~" delete-char
bindkey "^[[1~" beginning-of-line
bindkey "^[[4~" end-of-line

