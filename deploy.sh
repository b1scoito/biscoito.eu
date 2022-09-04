#!/bin/sh
USER=root
HOST=biscoito.eu
DIR=/var/www/biscoito.eu/public   # might sometimes be empty!

hugo && rsync -avz --delete public/ ${USER}@${HOST}:${DIR}

exit 0
