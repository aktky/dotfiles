# Go
export GOPATH=$HOME/go
export GOBIN=$GOPATH/bin
export PATH=$PATH:$GOPATH/bin
export GO111MODULE=on
export PATH=$PATH:/usr/local/go/bin

# Zig
export PATH="$HOME/dev/github.com/zigtools/zls/zig-out/bin:$PATH"

# Added by Windsurf
export PATH="/Users/aktky/.codeium/windsurf/bin:$PATH"

# Added by LM Studio CLI (lms)
export PATH="$PATH:/Users/aktky/.lmstudio/bin"
# End of LM Studio CLI section

# Created by `pipx` on 2025-03-24 07:56:58
export PATH="$PATH:/Users/aktky/.local/bin"

# fnm
eval "$(fnm env --use-on-cd --shell zsh)"

# bun completions
[ -s "/Users/aktky/.bun/_bun" ] && source "/Users/aktky/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# pyenv
eval "$(pyenv init -)"

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

alias dc="docker compose"
alias dcup="docker compose up"
alias dcrun="docker compose run"
alias dcps="docker compose ps"
alias dim="docker images"

alias reload="exec $SHELL -l"

alias ssh-add-id-rsa="ssh-add ~/.ssh/id_rsa"

alias jq_tr_cntrl='(){ echo "$1" | tr -d '[:cntrl:]' | jq . }'

autoload -U compinit
compinit -u
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
