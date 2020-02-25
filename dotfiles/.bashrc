#!/bin/bash
# .bashrc

# Source global definitions
# shellcheck disable=SC1091
[[ -r /etc/bashrc ]] && source /etc/bashrc

# If not running interactively, don't do anything
case $- in
  *i*) ;;
  *) return;;
esac

## History config
### don't put duplicate lines or lines starting with space in the history.
HISTCONTROL="ignoreboth:erasedups"
### append to the history file, don't overwrite it
shopt -s histappend
### for setting history length see HISTSIZE and HISTFILESIZE in bash
HISTSIZE="5000"
HISTFILESIZE=${HISTSIZE}
HISTTIMEFORMAT="%h %d %H:%M:%S >  "
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
fi

### Functions
# get current branch in git repo
function __parse_git_branch() {
  if [[ -x $( command -v git ) ]]; then
    BRANCH=$( git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/' )
    [[ -n "${BRANCH}" ]] && printf '%s' "[ $( __parse_git_dirty ) ${BRANCH}]"
    else
      return
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
    printf '%s' "${bits}"
  else
    return
  fi
}

# Aliases
alias ll='ls -l'
alias wget='wget -c'

# Vars
## bash prompt
export PS1="\[\e[33m\]\u\[\e[m\]\[\e[36m\]@\[\e[m\]\[\e[32m\]\h\[\e[m\]\[\e[31m\]:\[\e[m\]\[\e[36m\]\W\[\e[m\]\[\e[31;43m\]\$(__parse_git_branch)\[\e[m\]\[\e[32m\]\\$\[\e[m\] "
## colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

export PATH=$GOPATH/bin:$PATH
[[ $( systemd-path user-binaries ) ]] && \
  PATH="$(systemd-path user-binaries):$PATH" && \
  export PATH

## editor
export EDITOR="vim"
export VISUAL="vim"
# for git gpg
GPG_TTY=$( tty )
  export GPG_TTY
