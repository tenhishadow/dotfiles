#!/bin/bash
# .bashrc

# Source global definitions
# shellcheck disable=SC1091
[[ -r /etc/bashrc ]] && source /etc/bashrc

# If not running interactively, don't do anything
[[ $- == *i* ]] || return

## History config
### don't put duplicate lines or lines starting with space in the history.
HISTCONTROL="ignoreboth"
HISTSIZE="30000"
HISTFILESIZE=${HISTSIZE}
HISTTIMEFORMAT="%h %d %H:%M:%S >  "
# Ensure synchronization between shells by appending history after each command
PROMPT_COMMAND="history -a;$PROMPT_COMMAND"
### append to the history file, don't overwrite it
shopt -s histappend
### check the window size after each command and, if necessary, update the values of LINES and COLUMNS.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
{ [[ -z "${debian_chroot:-}" ]] && [[ -r /etc/debian_chroot ]]; } && \
  debian_chroot=$(cat /etc/debian_chroot)

# enable color support of ls and also add handy aliases
if { [[ -x /usr/bin/dircolors ]] && [[ ! "$OSTYPE" == "darwin"* ]]; }; then
  if [[ -r " ~/.dircolors" ]]; then
    eval "$(dircolors -b ~/.dircolors)"
  else
    eval "$(dircolors -b)"
  fi
  alias egrep='egrep --color=auto'
  alias fgrep='fgrep --color=auto'
  alias grep='grep --color=auto'
  alias ls='ls --color=auto'
  alias ip='ip -color=auto'
  alias diff='diff --color=auto'
fi

### Functions
# get current branch in git repo
function __parse_git_branch() {
  if [[ -x $( command -v git ) ]]; then
    branch=$( git symbolic-ref HEAD 2>/dev/null | awk -F '/' '{print $NF}' )
    [[ -n "${branch}" ]] && printf '%s' "[ $( __parse_git_dirty )${branch} ]"
  fi
}
# get current status of git repo
function __parse_git_dirty {
  status=$( LC_ALL=C git status 2>&1 | tee )
  dirty=$( printf '%s' "${status}" 2> /dev/null | grep "modified:" &> /dev/null; printf '%s\n' "$?" )
  untracked=$( printf '%s'/ "${status}" 2> /dev/null | grep "Untracked files" &> /dev/null; printf '%s\n' "$?" )
  ahead=$( printf '%s'/ "${status}" 2> /dev/null | grep "Your branch is ahead of" &> /dev/null; printf '%s\n' "$?" )
  newfile=$( printf '%s'/ "${status}" 2> /dev/null | grep "new file:" &> /dev/null; printf '%s\n' "$?" )
  renamed=$( printf '%s'/ "${status}" 2> /dev/null | grep "renamed:" &> /dev/null; printf '%s\n' "$?" )
  deleted=$( printf '%s'/ "${status}" 2> /dev/null | grep "deleted:" &> /dev/null; printf '%s\n' "$?" )
  unset bits

  [[ "${renamed}" == "0" ]]   && bits=">${bits}"
  [[ "${ahead}" == "0" ]]     && bits="*${bits}"
  [[ "${newfile}" == "0" ]]   && bits="+${bits}"
  [[ "${untracked}" == "0" ]] && bits="?${bits}"
  [[ "${deleted}" == "0" ]]   && bits="x${bits}"
  [[ "${dirty}" == "0" ]]     && bits="!${bits}"
  if [[ -n "${bits}" ]]; then
    printf '%s' "${bits} "
  else
    return
  fi
}

# find and sort files by size in directory( current by default )
# shellcheck disable=SC2317  # Don't warn about unreachable commands in this function
function duu() {
  find . \
    -maxdepth 1 \
    -exec \
      du -sm '{}' \; | \
    sort -n
}

# AWS: user/account-id
function aws-whoami() {
  [[ ! $( command -v aws ) ]] && \
    printf '%s\n' 'please install AWS CLI' && \
    return 1
  [[ ! $( command -v jq ) ]] && \
    printf '%s\n' 'please install jq' && \
    return 1
  aws sts get-caller-identity \
    | jq -r '.Arn' \
    | awk -F ':' '{ print $NF, $(NF-1)}'
}

# record screen with vlc
function recit() {
  __SCREEN_RECORD_DIR="${HOME}/Videos/RecScreen"
  [[ ! -d ${__SCREEN_RECORD_DIR} ]] &&
    mkdir -p "${__SCREEN_RECORD_DIR}"
  _REC_OUT=$(pactl get-default-sink)




  cvlc \
    -I dummy -q \
    --screen-fps=24.000000 --live-caching=300 screen:// \
    --input-slave="pulse://${_REC_OUT}.monitor" \
    --input-slave="pulse://${_REC_IN}" \
    --sout "#transcode{vcodec=h264,acodec=aac,channels=2,samplerate=48000}:standard{mux=mp4,dst=""${__SCREEN_RECORD_DIR}/rec-${1}-$(date +%Y-%m-%d-%H%M).mp4"",access=file}" \
    vlc://quit
}

# temp dirs for temp things
function poc() {
  POCCTL="/tmp/poc-${USER}"
  case "${1}" in
  "")
    POCDIR="/tmp/${RANDOM}"
    mkdir -p ${POCDIR}
    echo "${POCDIR}" >> "${POCCTL}"
    cd ${POCDIR} || exit 1
    PS1="PoC-${POCDIR}-${PS1}"
    ;;
  "list")
    echo "PoC dirs:"
    [[ -r ${POCCTL} ]] && cat "${POCCTL}"
    ;;
  *)
    echo "4to?"
    ;;
  esac
}

# du
function duu() {
  find . \
    -maxdepth 1 \
    -exec \
      du -sm '{}' \; | \
    sort -n
}

# Aliases
alias ll='ls -l'
alias wget='wget -c'
alias aws-whereami='aws configure get region'
alias open='xdg-open'
alias copy='xclip -selection clipboard -in'
alias paste='xclip -selection clipboard -out'
alias kube-temp='kubectl run -it --rm --image debian:bookworm tmp-${RANDOM} -- bash'
alias archupdate='yay -Syu --noconfirm; yay -Scc --noconfirm'

# better cat
# [[ -x $( command -v bat ) ]] && \
#   alias cat='bat -pf --paging=never'
# Vars
## bash prompt
export PS1="\[\e[33m\]\u\[\e[m\]\[\e[36m\]@\[\e[m\]\[\e[32m\]\h\[\e[m\]\[\e[31m\]:\[\e[m\]\[\e[36m\]\W\[\e[m\]\[\e[31;43m\]\$(__parse_git_branch)\[\e[m\]\[\e[32m\]\\$\[\e[m\] "
## colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
## editor
export EDITOR="vim"
export VISUAL="${EDITOR}"
# for git gpg
GPG_TTY=$( tty )
  export GPG_TTY

set_less_termcap() {
    local var_name=$1
    shift
    value=$(tput "$@")
    export "$var_name"="$value"
}

# Set LESS_TERMCAP variables with specific colors
set_less_termcap LESS_TERMCAP_ZN ssubm                # ZN (subscript) | Changes text to subscript
set_less_termcap LESS_TERMCAP_ZO ssupm                # ZO (superscript) | Changes text to superscript
set_less_termcap LESS_TERMCAP_ZV rsubm                # ZV (end subscript) | Resets subscript mode to default
set_less_termcap LESS_TERMCAP_ZW rsupm                # ZW (end superscript) | Resets superscript mode to default
set_less_termcap LESS_TERMCAP_mb bold setaf 3         # mb (blink) | High-intensity yellow
set_less_termcap LESS_TERMCAP_md bold setaf 10        # md (bold) | High-intensity green
set_less_termcap LESS_TERMCAP_me sgr0                 # me (end mode) | Resets all attributes to default
set_less_termcap LESS_TERMCAP_mh dim                  # mh (half-bright) | Makes text half as bright
set_less_termcap LESS_TERMCAP_mr rev                  # mr (reverse) | Inverts foreground and background colors
set_less_termcap LESS_TERMCAP_se rmso sgr0            # se (end standout) | Resets standout mode to default
set_less_termcap LESS_TERMCAP_so bold setaf 7 setab 4 # so (standout) | White text on a blue background
set_less_termcap LESS_TERMCAP_ue rmul sgr0            # ue (end underline) | Resets underline mode to default
set_less_termcap LESS_TERMCAP_us smul setaf 15        # us (start underline) | High-intensity white

PAGER="less -RFMIX"
  export PAGER

# PATH extends
## systemd user-binaries
if [[ "${OSTYPE}" != darwin* ]]; then
  [[ $(systemd-path user-binaries) ]] && \
    PATH="$(systemd-path user-binaries):$PATH"
fi

## rbenv
[[ -x $( command -v rbenv ) ]] && \
  eval "$(rbenv init -)"

## go
GOPATH="${HOME}/go" && \
  export GOPATH
[[ ! -d "${GOPATH}" ]] && \
  mkdir "${GOPATH}"
PATH=$GOPATH/bin:$PATH

###
# completions
## complete hashicorp-tools
for hashicorp_tool in consul terraform vault packer; do
  [[ -x $( command -v ${hashicorp_tool} ) ]] && \
    complete -C "$( command -v ${hashicorp_tool} )" ${hashicorp_tool}
done
## complete github cli
[[ -x $( command -v gh ) ]] && \
  eval "$( gh completion -s bash )"
# complete awscli
[[ -x "$( command -v aws_completer )" ]] && \
  complete -C "$( command -v aws_completer )" aws
# complete kubectl
# shellcheck disable=SC1090
[[ -x "$( command -v kubectl 2>/dev/null)" ]] && \
  source <(kubectl completion bash)
# complete docker
# shellcheck disable=SC1090
[[ -x "$( command -v docker )" ]] && \
  source /usr/share/bash-completion/bash_completion && \
  source <(docker completion bash)
# complete helm
# shellcheck disable=SC1090
[[ -x "$( command -v helm )" ]] && \
  source <(helm completion bash 2>/dev/null)
# GVM is the Go Version Manager
[[ -s "${HOME}/.gvm/scripts/gvm" ]] && source "${HOME}/.gvm/scripts/gvm"

# ssh-agent
SSH_AUTH_SOCK=/run/user/$(id -u)/ssh-agent.socket
export SSH_AUTH_SOCK;
# BEGIN_KITTY_SHELL_INTEGRATION
if test -n "$KITTY_INSTALLATION_DIR" -a -e "$KITTY_INSTALLATION_DIR/shell-integration/bash/kitty.bash"; then source "$KITTY_INSTALLATION_DIR/shell-integration/bash/kitty.bash"; fi
# END_KITTY_SHELL_INTEGRATION

## final PATH export
export PATH

# OCTAVIA CLI 0.44.4
OCTAVIA_ENV_FILE=/home/tenhi/.octavia
