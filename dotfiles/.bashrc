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
  if [[ ! $(type -P git) || ! -d "$git_dir" ]]; then
    return
  fi
  # get branch
  local branch
  if [[ -f "${git_dir}/HEAD" ]]; then
    branch=$(awk -F 'ref: refs/heads/' '{print $NF}' "${git_dir}/HEAD")
  else
    branch="detached"
  fi
  # get branch stats
  local stats=$(git rev-list --count --left-right "HEAD...@{upstream}" 2>/dev/null)
  local ahead behind
  read -r behind ahead <<<"${stats}"
  local status_output=""
  local stashes=$(git stash list 2>/dev/null | awk 'END {print NR}')
  local conflicts=$(git diff --name-only --diff-filter=U 2>/dev/null | awk 'END {print NR}')
  local staged=$(git diff --cached --name-only 2>/dev/null | awk 'END {print NR}')
  local unstaged=$(git diff --name-only 2>/dev/null | awk 'END {print NR}')
  local untracked=$(git ls-files --others --exclude-standard 2>/dev/null | awk 'END {print NR}')

  ((ahead > 0)) && status_output+="⇡${ahead} "
  ((behind > 0)) && status_output+="⇣${behind} "
  ((stashes > 0)) && status_output+="*${stashes} "
  ((conflicts > 0)) && status_output+="~${conflicts} "
  ((staged > 0)) && status_output+="+${staged} "
  ((unstaged > 0)) && status_output+="!${unstaged} "
  ((untracked > 0)) && status_output+="?${untracked} "

  # make an output
  printf "\e[100;96m[ %s %s ]\e[0m " "$status_output" "$branch"
}

# find and sort files by size in directory( current by default )
# shellcheck disable=SC2317  # Don't warn about unreachable commands in this function
function duu() {
  find . \
    -maxdepth 1 \
    -exec \
    du -sm '{}' \; |
    sort -n
}

# AWS: user/account-id
function aws-whoami() {
  [[ ! $(type -P aws) ]] &&
    printf '%s\n' 'please install AWS CLI' &&
    return 1
  [[ ! $(type -P jq) ]] &&
    printf '%s\n' 'please install jq' &&
    return 1
  aws sts get-caller-identity |
    jq -r '.Arn' |
    awk -F ':' '{ print $NF, $(NF-1)}'
}
function az-whoami() {
  [[ ! $(type -P az) ]] &&
    printf '%s\n' 'please install az' &&
    return 1
  az account show
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
    echo "${POCDIR}" >>"${POCCTL}"
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
    du -sm '{}' \; |
    sort -n
}

function change_git_remote_protocol() {
  local origin_url=$(git remote get-url origin 2>/dev/null)
  local status=$?
  local protocol_type
  local new_url

  [[ $status -ne 0 ]] &&
    echo "Failed to get git remote URL" &&
    return 1

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
    $(type -P top)
    return
    ;;
  esac

  if [[ -x $(type -P bashtop) ]]; then
    bashtop
  elif [[ -x $(type -P bpytop) ]]; then
    bpytop
  elif [[ -x $(type -P htop) ]]; then
    htop
  elif [[ -x $(type -P top) ]]; then
    # shellcheck disable=SC2091
    $(type -P top)
  else
    echo "no top installed"
    return 1
  fi
}

function temp() {
  printf "dev\t\ttype\ttemp\tserial\t\t\t\t\tmodel\n"
  for disk in /dev/sd[a-z] /dev/nvme[0-9]; do
    [[ -c "$disk" || -b "$disk" ]] &&
      sudo smartctl --all --json "$disk" |
      jq -r '
          .device.name + "\t" +
          .device.type + "\t" +
          (.temperature.current | tostring) + "C\t" +
          .serial_number + "\t\t\t" +
          .model_name
          '
  done
}

function check_nvme() {
  [[ ! -x $(type -P nvme) ]] &&
    echo "ERR: nvme-cli is not installed" &&
    return 1
  [[ -z "${1}" ]] &&
    echo "ERR: arg1 is required (disk)" &&
    return 1
  [[ ! -c "${1}" ]] &&
    echo "ERR: arg1 must be nvme root device" &&
    return 1
  sudo nvme id-ctrl "${1}"
  sudo nvme smart-log "${1}"
  sudo nvme error-log "${1}" --log-entries=64
  sudo nvme id-ctrl "${1}" | grep -iE 'oncs|fna|vwc|sanicap'
  sudo nvme get-log "${1}" --log-id=2 --log-len=512 --raw-binary | hexdump -C | head -n 40
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
alias copy='wl-copy'
alias paste='wl-paste'
alias kube-temp='kubectl run -it --rm --image debian:trixie tmp-${RANDOM} -- bash'
alias archupdate='yay -Syu --noconfirm; yay -Scc --noconfirm'
alias arch-rekey='sudo pacman-key --refresh-keys'
alias dotfiles-update='cd ~/.dotfiles/ && git pull && pipenv sync && pipenv run install'
alias ans-workstation-update='cd ~/.ans-workstation/ && git pull && pipenv sync && pipenv run install'
alias tgfmt='terragrunt hcl format --non-interactive'
alias tfmt='terraform fmt -recursive -diff'
alias vim='nvim'
alias vimdiff='nvim -d'
alias nmap-fast='sudo nmap -sS -p- -T5 -Pn'
alias nmap-slow='sudo nmap -sS -p- -T0 -Pn'
## clear
alias clear-journald='sudo journalctl --rotate && sudo journalctl --vacuum-time=1s'
alias clear-vim='rm -rf ~/.vim/autoload/ ~/.vim/plugged/'
alias clear-nvim='rm -rf $HOME/.local/share/nvim $HOME/.config/nvim $HOME/.cache/nvim $HOME/.local/state/nvim/'

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
export EDITOR="nvim"
export VISUAL="${EDITOR}"
# for git gpg
GPG_TTY=$(tty)
export GPG_TTY

export LESS_TERMCAP_mb=$(
  tput bold
  tput setaf 2
) # green
export LESS_TERMCAP_md=$(
  tput bold
  tput setaf 6
) # cyan
export LESS_TERMCAP_me=$(tput sgr0)
export LESS_TERMCAP_so=$(
  tput bold
  tput setaf 3
  tput setab 4
) # yellow on blue
export LESS_TERMCAP_se=$(
  tput rmso
  tput sgr0
)
export LESS_TERMCAP_us=$(
  tput smul
  tput bold
  tput setaf 7
) # white
export LESS_TERMCAP_ue=$(
  tput rmul
  tput sgr0
)
export LESS_TERMCAP_mr=$(tput rev)
export LESS_TERMCAP_mh=$(tput dim)
export LESS_TERMCAP_ZN=$(tput ssubm)
export LESS_TERMCAP_ZV=$(tput rsubm)
export LESS_TERMCAP_ZO=$(tput ssupm)
export LESS_TERMCAP_ZW=$(tput rsupm)
export GROFF_NO_SGR=1 # For Konsole and Gnome-terminal
# shellcheck disable=SC2016
export LESS='-R --use-color -Dd+r$Du+b$'

PAGER="less -RFMIX"
export PAGER

# PATH extends
## systemd user-binaries
if [[ "${OSTYPE}" != darwin* ]]; then
  [[ $(systemd-path user-binaries) ]] &&
    PATH="$(systemd-path user-binaries):$PATH"
fi

## rbenv
[[ -x $(type -P rbenv) ]] &&
  eval "$(rbenv init -)"

## go
GOPATH="${HOME}/go" &&
  export GOPATH
[[ ! -d "${GOPATH}" ]] &&
  mkdir "${GOPATH}"
PATH=$GOPATH/bin:$PATH

## google cloud
[[ ! -d "/opt/google-cloud-cli/bin" ]] &&
  PATH="$PATH:/opt/google-cloud-cli/bin"

###
# completions
## complete hashicorp-tools
for hashicorp_tool in consul terraform vault packer; do
  [[ -x $(type -P ${hashicorp_tool}) ]] &&
    complete -C "$(type -P ${hashicorp_tool})" ${hashicorp_tool}
done
## complete github cli
[[ -x $(type -P gh) ]] &&
  eval "$(gh completion -s bash)"
# complete awscli
[[ -x "$(type -P aws_completer)" ]] &&
  complete -C "$(type -P aws_completer)" aws
# complete kubectl
# shellcheck disable=SC1090
[[ -x "$(type -P kubectl 2>/dev/null)" ]] &&
  source <(kubectl completion bash)
# complete docker
# shellcheck disable=SC1090
[[ -x "$(type -P docker)" ]] &&
  source /usr/share/bash-completion/bash_completion &&
  source <(docker completion bash)
# complete helm
# shellcheck disable=SC1090
[[ -x "$(type -P helm)" ]] &&
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
