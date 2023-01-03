# Go
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH=$PATH:$GOPATH/bin
export GO111MODULE=on
export PATH=$PATH:/usr/local/go/bin

# Homebrew
eval "$(/opt/homebrew/bin/brew shellenv)"

# fnm
eval "$(fnm env --use-on-cd)"


# Flutter
export PATH="$PATH:$HOME/development/flutter/bin"

# pyenv
export PYENV_ROOT=${HOME}/.pyenv
if [ -d "${PYENV_ROOT}" ]; then
    export PATH=${PYENV_ROOT}/bin:$PATH
    eval "$(pyenv init -)"
fi

# General
export PATH=/usr/local/bin:$PATH
export PROMPT='%~ %# '

setopt nonomatch

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

alias k="kubectl"
alias kgp="kubectl get pods"
alias kgs="kubectl get svc"
alias kgi="kubectl get ing"

alias dc="docker-compose"
alias dcup="docker-compose up"
alias dcrun="docker-compose run"
alias dcps="docker-compose ps"
alias dim="docker images"

alias reload="exec $SHELL -l"

alias ssh-add-id-rsa="ssh-add ~/.ssh/id_rsa"

alias ngrok="~/dev/ngrok/ngrok"

autoload -U compinit
compinit -u
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/aktky/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/aktky/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/aktky/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/aktky/google-cloud-sdk/completion.zsh.inc'; fi
