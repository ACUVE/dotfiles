# The following lines were added by compinstall

zstyle ':completion:*' expand prefix suffix
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-suffixes true
zstyle ':completion:*' original true
zstyle ':completion:*' squeeze-slashes true

autoload -Uz compinit; compinit
# End of lines added by compinstall
# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=10000000
SAVEHIST=10000000
# End of lines configured by zsh-newuser-install

autoload -Uz colors; colors
zstyle ':completion:*:default' menu select=2
zstyle ':completion:*' ignore-parents parent pwd ..
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
setopt auto_cd                  # フォルダ名だけでcd
setopt auto_pushd
setopt auto_menu
setopt auto_list
setopt list_packed
setopt list_types
setopt correct
setopt magic_equal_subst
setopt extended_history
setopt extendedglob
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_reduce_blanks
setopt inc_append_history
setopt share_history
disable r
stty stop undef

bindkey -e
bindkey "^?"    backward-delete-char
bindkey "^H"    backward-delete-char
bindkey "^[[3~" delete-char
bindkey "^[[1~" beginning-of-line
bindkey "^[[4~" end-of-line
bindkey "^[[Z" reverse-menu-complete

### Aliases ###
autoload -Uz zmv
alias ls="ls --color=auto -F"
alias la="ls -la"
alias lsa="ls -a"
alias lsl="ls -l"
alias ll="ls -l"
alias less="less -R"
alias j="z"
alias g="git"
alias mmv="noglob zmv -W"

### cdしたら勝手にls ###
# function cd(){
    # builtin cd $@ && ls > $TTY 2> /dev/null;
# }

### z.sh ###
if [ -f ~/.zsh/z/z.sh ]; then
    source ~/.zsh/z/z.sh
fi

### プロンプト ###
setopt transient_rprompt
if [ ${UID} -eq 0 ]; then
    PROMPTCOLOR="red"
elif [ -n "${SSH_CONNECTION}" ]; then
    PROMPTCOLOR="yellow"
else
    PROMPTCOLOR="green"
fi
PROMPT="%E[%B%F{${PROMPTCOLOR}}%n%b%f%F{${PROMPTCOLOR}}@%m%f] %~"$'\n'"%# "
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
autoload -U add-zsh-hook
add-zsh-hook precmd _update_vcs_info_msg
RPROMPT="%1(v|%F{green}%1v%f|)"

# https://github.com/pypa/pipenv/issues/1058
export SHELL=`which zsh`
export PIPENV_SHELL=`which zsh`

## Read .proxy
if [ -e ~/.proxy ]; then
    source ~/.proxy
fi

## Read .env
if [ -e ~/.env ]; then
    source ~/.env
fi
