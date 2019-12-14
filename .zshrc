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

# Aliases
alias g="git"
alias gch="git checkout"
alias gsw="git switch"
alias ga="git add"
alias gcm="git commit -m"
alias gb="git branch"
alias gpl="git pull"
alias gps="git push"
alias gst="git status"
alias gdf="git diff"

# 補完
autoload -U compinit
compinit -u
