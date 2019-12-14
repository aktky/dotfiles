# Go
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH=$PATH:$GOPATH/bin
export GO111MODULE=on

# goenv
export PATH=$HOME/.goenv/bin:$PATH
export GOENV_DISABLE_GOPATH=1
eval "$(goenv init -)"

# direnv
export EDITOR=vim
eval "$(direnv hook zsh)"

# General
export PATH=/usr/local/bin:$PATH
export PROMPT='%~ %# '
