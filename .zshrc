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
HISTSIZE=10000
SAVEHIST=10000
# End of lines configured by zsh-newuser-install

zstyle ':completion:*' ignore-parents parent pwd ..
setopt auto_cd
setopt auto_list
setopt correct
setopt magic_equal_subst
setopt extended_history
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_reduce_blanks
disable r

bindkey -e
bindkey "^?"    backward-delete-char
bindkey "^H"    backward-delete-char
bindkey "^[[3~" delete-char
bindkey "^[[1~" beginning-of-line
bindkey "^[[4~" end-of-line
bindkey "^[[Z" reverse-menu-complete

### Aliases ###
alias la="ls -la"

