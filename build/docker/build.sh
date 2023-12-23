#!/bin/bash

REPOTAG="salsevensix/serverjockey:${1}"

[ "$(whoami)" = "root" ] || exit 1
cd "$(dirname $0)" || exit 1
[ -f Dockerfile ] || exit 1
[ -f entrypoint.sh ] || exit 1
[ -f sjgms.deb ] || exit 1
docker rmi $REPOTAG > /dev/null 2>&1
docker system prune -f
docker build --no-cache -t $REPOTAG . || exit 1
docker login || exit 1
docker push $REPOTAG || exit 1

exit 0
