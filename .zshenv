### golang ###
GOPATH_MAIN=$HOME/go
export GOPATH="${GOPATH_MAIN}:$HOME/Sync/project/Go"

### PATH ###
path=(
    $GOPATH_MAIN/bin(N-/)
    $path
)
