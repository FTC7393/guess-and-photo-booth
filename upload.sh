#!/bin/bash
cd `dirname $0`
rsync -aPi --delete ./ rizzpi:guess/ --exclude .venv/ --exclude __pycache__/ --exclude data/ $@
if ! echo $@ | grep -- --dry-run > /dev/null; then
    echo 'restarting service'
    ssh rizzpi sudo systemctl restart guess
fi