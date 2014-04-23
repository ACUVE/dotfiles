# The following lines were added by compinstall

zstyle ':completion:*' expand prefix suffix
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-suffixes true
zstyle ':completion:*' original true
zstyle ':completion:*' squeeze-slashes true
zstyle :compinstall filename '/home/acuve/.zshrc'

autoload -Uz compinit; compinit
autoload -Uz colors; colors
# End of lines added by compinstall
# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=10000
SAVEHIST=10000
# End of lines configured by zsh-newuser-install

zstyle ':completion:*' ignore-parents parent pwd ..
setopt auto_cd
setopt auto_list
# setopt correct
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

### auto-fu ###
if [ -f ~/.zsh/auto-fu.zsh/auto-fu.zsh ]; then
    source ~/.zsh/auto-fu.zsh/auto-fu.zsh
    function zle-line-init () {
        auto-fu-init
    }
    zle -N zle-line-init
    zstyle ':auto-fu:var' postdisplay $''
fi

### プロンプト ###
PROMPT="%E[%B%F{green}%n%b%f%F{green}@%m%f] %~"$'\n'"%# "
autoload -Uz vcs_info
zstyle ':vcs_info:*' enable git svn hg bzr
zstyle ':vcs_info:*' formats '(%s)-[%b]'
zstyle ':vcs_info:*' actionformats '(%s)-[%b|%a]'
zstyle ':vcs_info:(svn|bzr):*' branchformat '%b:r%r'
zstyle ':vcs_info:bzr:*' use-simple true

autoload -Uz is-at-least
if is-at-least 4.3.10; then
    zstyle ':vcs_info:git:*' check-for-changes true
    zstyle ':vcs_info:git:*' stagedstr "+"    # 適当な文字列に変更する
    zstyle ':vcs_info:git:*' unstagedstr "-"  # 適当の文字列に変更する
    zstyle ':vcs_info:git:*' formats '(%s)-[%b] %c%u'
    zstyle ':vcs_info:git:*' actionformats '(%s)-[%b|%a] %c%u'
fi

function _update_vcs_info_msg() {
    psvar=()
    LANG=en_US.UTF-8 vcs_info
    [[ -n "$vcs_info_msg_0_" ]] && psvar[1]="$vcs_info_msg_0_"
}
add-zsh-hook precmd _update_vcs_info_msg
RPROMPT="%1(v|%F{green}%1v%f|)"
