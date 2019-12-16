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
alias dcrm="docker-compose rm"
alias dcps="docker-compose ps"

# 補完
autoload -U compinit
compinit -u
# 補完で大文字・小文字を区別しない
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/aktky/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/aktky/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/aktky/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/aktky/google-cloud-sdk/completion.zsh.inc'; fi
