#!/bin/sh
# Push main using a token file (never printed). Usage: scripts/push.sh /path/to/tokenfile
T=$(cat "$1"); B=$(printf 'YuvalHir:%s' "$T" | base64 -w0)
git -c http.extraheader="Authorization: Basic $B" push https://github.com/YuvalHir/open-count-model.git main ${2:+"$2"}
