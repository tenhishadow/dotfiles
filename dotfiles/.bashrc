#!/bin/bash
# .bashrc
# shellcheck disable=SC2155
# vim:ft=bash

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
shopt -s promptvars

### Functions
___git_status() {
  # check | git
  local git_dir
  git_dir=$(git rev-parse --git-dir 2>/dev/null)
  if [[ ! $(command -v git) || ! -d "$git_dir" ]]; then
    return
  fi
  # get branch
  local branch
  if [[ -f "${git_dir}/HEAD" ]]; then
    branch=$( awk -F 'ref: refs/heads/' '{print $NF}' "${git_dir}/HEAD")
  else
    branch="detached"
  fi
  # get branch stats
  local stats=$(git rev-list --count --left-right "HEAD...@{upstream}" 2>/dev/null)
  local ahead behind
  read -r behind ahead <<< "${stats}"
  local status_output=""
  local stashes=$(git stash list 2>/dev/null | awk 'END {print NR}')
  local conflicts=$(git diff --name-only --diff-filter=U 2>/dev/null | awk 'END {print NR}')
  local staged=$(git diff --cached --name-only 2>/dev/null | awk 'END {print NR}')
  local unstaged=$(git diff --name-only 2>/dev/null | awk 'END {print NR}')
  local untracked=$(git ls-files --others --exclude-standard 2>/dev/null | awk 'END {print NR}')

  (( ahead > 0 )) && status_output+="⇡${ahead} "
  (( behind > 0 )) && status_output+="⇣${behind} "
  (( stashes > 0 )) && status_output+="*${stashes} "
  (( conflicts > 0 )) && status_output+="~${conflicts} "
  (( staged > 0 )) && status_output+="+${staged} "
  (( unstaged > 0 )) && status_output+="!${unstaged} "
  (( untracked > 0 )) && status_output+="?${untracked} "

  # make an output
  printf "\e[100;96m[ %s %s ]\e[0m " "$status_output" "$branch"
}

# git cleanup | remove all, but not default branch
function git_clean_to_default() {
  [[ ! -d '.git' ]] \
    && echo 'not a git repo' \
    && return
  local _default_git_branch=$(git symbolic-ref refs/remotes/origin/HEAD \
    | sed 's#refs/remotes/origin/##' )
  # checkout to default one
  # git checkout $_default_git_branch
  for i in $(git branch --format="%(refname:short)" | grep -v $_default_git_branch); do
    echo removing $i
  done
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
    PS1="\[\e[44;37m\][ PoC \${POCDIR} ]\[\e[0m\] ${PS1}"
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

function change_git_remote_protocol() {
    local origin_url=$(git remote get-url origin 2>/dev/null)
    local status=$?
    local protocol_type
    local new_url

    [[ $status -ne 0 ]] \
      && echo "Failed to get git remote URL" \
      && return 1

    # check current proto
    if [[ $origin_url =~ ^https:// ]]; then
        protocol_type="https"
    elif [[ $origin_url =~ ^git@ ]]; then
        protocol_type="ssh"
    else
        echo "Unknown protocol type"
        return 1
    fi

    case $1 in
        "ssh")
            if [ "$protocol_type" == "https" ]; then
                new_url=$(echo "$origin_url" | awk -F'/' '{print "git@"$3":"$4"/"$5}')
                git remote set-url origin "$new_url"
            fi
            ;;
        "https")
            if [ "$protocol_type" == "ssh" ]; then
                new_url=$(echo "$origin_url" | awk -F':' '{sub(/^git@/, "", $1); print "https://"$1"/"$2}')
                git remote set-url origin "$new_url"
            fi
            ;;
        *)
            echo "Invalid argument. Use 'ssh' or 'https'."
            return 1
            ;;
    esac
}

# choose which top to exec
function top() {
  case $1 in
    "-c")
      # shellcheck disable=SC2091
      $( which top )
      return
      ;;
  esac

  if [[ -x $(command -v bashtop) ]]; then bashtop
  elif [[ -x $(command -v bpytop) ]]; then bpytop
  elif [[ -x $(command -v htop) ]]; then htop
  elif [[ -x $(which top) ]]; then
    # shellcheck disable=SC2091
    $( which top)
  else
    echo "no top installed"
    return 1
  fi
}

# Aliases
alias grep='ugrep'
alias ls='ls --color=auto'
alias ip='ip -color=auto'
alias diff='diff --color=auto'
alias ll='ls -l'
alias wget='wget -c'
alias aws-whereami='aws configure get region'
alias open='xdg-open'
alias copy='xclip -selection clipboard -in'
alias paste='xclip -selection clipboard -out'
alias kube-temp='kubectl run -it --rm --image debian:bookworm tmp-${RANDOM} -- bash'
alias archupdate='yay -Syu --noconfirm; yay -Scc --noconfirm'
alias dotfiles-update='cd ~/.dotfiles/ && git pull && pipenv sync && pipenv run install'
alias ans-workstation-update='cd ~/.ans-workstation/ && git pull && pipenv sync && pipenv run install'
alias vim-cleanup='rm -rf ~/.vim/autoload/ ~/.vim/plugged/'
alias tgfmt='terragrunt hclfmt --terragrunt-diff -all'
alias tfmt='terraform fmt -recursive -diff'

# Vars
## bash prompt
PS1='$(___git_status)'                           # git status
PS1+='\[\033[01;32m\]\u@\h\[\033[00m\] '         # green user@host
PS1+='\[\033[01;34m\]\w\[\033[00m\]'             # blue current working directory
PS1+='\n\[\033[01;$((31+!$?))m\]\$\[\033[00m\] ' # green/red (success/error) $/# (normal/root)
PS1+='\[\e]0;\u@\h: \w\a\]'                      # terminal title: user@host: dir

export PS1

## colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
## editor
export EDITOR="vim"
export VISUAL="${EDITOR}"
# for git gpg
GPG_TTY=$( tty )
  export GPG_TTY

export LESS_TERMCAP_mb=$(tput bold; tput setaf 2) # green
export LESS_TERMCAP_md=$(tput bold; tput setaf 6) # cyan
export LESS_TERMCAP_me=$(tput sgr0)
export LESS_TERMCAP_so=$(tput bold; tput setaf 3; tput setab 4) # yellow on blue
export LESS_TERMCAP_se=$(tput rmso; tput sgr0)
export LESS_TERMCAP_us=$(tput smul; tput bold; tput setaf 7) # white
export LESS_TERMCAP_ue=$(tput rmul; tput sgr0)
export LESS_TERMCAP_mr=$(tput rev)
export LESS_TERMCAP_mh=$(tput dim)
export LESS_TERMCAP_ZN=$(tput ssubm)
export LESS_TERMCAP_ZV=$(tput rsubm)
export LESS_TERMCAP_ZO=$(tput ssupm)
export LESS_TERMCAP_ZW=$(tput rsupm)
export GROFF_NO_SGR=1         # For Konsole and Gnome-terminal
# shellcheck disable=SC2016
export LESS='-R --use-color -Dd+r$Du+b$'

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
# complete fzf
for fzf_config in key-bindings completion; do
  # shellcheck disable=SC1090
  [[ -r "/usr/share/fzf/${fzf_config}.bash" ]] && source "/usr/share/fzf/${fzf_config}.bash"
done
# BEGIN_KITTY_SHELL_INTEGRATION
if test -n "$KITTY_INSTALLATION_DIR" -a -e "$KITTY_INSTALLATION_DIR/shell-integration/bash/kitty.bash"; then source "$KITTY_INSTALLATION_DIR/shell-integration/bash/kitty.bash"; fi
# END_KITTY_SHELL_INTEGRATION

## final PATH export
export PATH
