# .bashrc

# Source global definitions
[[ -r /etc/bashrc ]] && source /etc/bashrc

# If not running interactively, don't do anything
case $- in
  *i*) ;;
  *) return;;
esac

# Basic bash config

## History config
### don't put duplicate lines or lines starting with space in the history.
HISTCONTROL="ignoreboth"
### append to the history file, don't overwrite it
shopt -s histappend
### for setting history length see HISTSIZE and HISTFILESIZE in bash
HISTSIZE="5000"
HISTFILESIZE="20000"
### check the window size after each command and, if necessary, update the values of LINES and COLUMNS.
shopt -s checkwinsize

# make less more friendly for non-text input files, see lesspipe
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
  debian_chroot=$(cat /etc/debian_chroot)
fi

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
  if [[ -r " ~/.dircolors" ]]; then
    eval "$(dircolors -b ~/.dircolors)"
  else
    eval "$(dircolors -b)"
  fi
  alias dir='dir --color=auto'
  alias egrep='egrep --color=auto'
  alias fgrep='fgrep --color=auto'
  alias grep='grep --color=auto'
  alias ls='ls --color=auto'
fi

### Functions
# get current branch in git repo
function __parse_git_branch() {
  BRANCH=$( git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/' )
  [[ ! "${BRANCH}" == "" ]] && STAT=$( __parse_git_dirty ) && echo "[${BRANCH}${STAT}]"
}

# get current status of git repo
function __parse_git_dirty {
  status=$( git status 2>&1 | tee )
  dirty=$( echo -n "${status}" 2> /dev/null | grep "modified:" &> /dev/null; echo "$?" )
  untracked=$( echo -n "${status}" 2> /dev/null | grep "Untracked files" &> /dev/null; echo "$?" )
  ahead=$( echo -n "${status}" 2> /dev/null | grep "Your branch is ahead of" &> /dev/null; echo "$?" )
  newfile=$( echo -n "${status}" 2> /dev/null | grep "new file:" &> /dev/null; echo "$?" )
  renamed=$( echo -n "${status}" 2> /dev/null | grep "renamed:" &> /dev/null; echo "$?" )
  deleted=$( echo -n "${status}" 2> /dev/null | grep "deleted:" &> /dev/null; echo "$?" )
  bits=''
  if [ "${renamed}" == "0" ]
    then bits=">${bits}"
  elif [ "${ahead}" == "0" ]
    then bits="*${bits}"
  elif [ "${newfile}" == "0" ]
    then bits="+${bits}"
  elif [ "${untracked}" == "0" ]
    then bits="?${bits}"
  elif [ "${deleted}" == "0" ]
    then bits="x${bits}"
  elif [ "${dirty}" == "0" ]
    then bits="!${bits}"
  elif [ ! "${bits}" == "" ]
    then echo " ${bits}"
  else
    echo ""
  fi
}

# Aliases
alias ls='ls --color=auto'
alias ll='ls -l'
## terraform
alias terraform-hook='for i in *.tf; do terraform fmt $i; done && terraform-docs --sort-inputs-by-required md ./ > README.md'


# Vars
## bash prompt
export PS1="\[\e[33m\]\u\[\e[m\]\[\e[36m\]@\[\e[m\]\[\e[32m\]\h\[\e[m\]\[\e[31m\]:\[\e[m\]\[\e[36m\]\W\[\e[m\]\[\e[31;43m\]\$(__parse_git_branch)\[\e[m\]\[\e[32m\]\\$\[\e[m\] "
## colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
## golang
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$GOPATH/bin:$PATH
## editor
export EDITOR="vim"
export VISUAL="vim"
# for git gpg
GPG_TTY=$( tty ) && export GPG_TTY

