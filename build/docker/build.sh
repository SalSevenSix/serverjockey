#!/bin/bash

echo "Initialising docker build process"
[ "$(whoami)" = "root" ] || exit 1
which docker > /dev/null || exit 1
REPOTAG="salsevensix/serverjockey:${1}"
cd "$(dirname $0)" || exit 1
[ -f Dockerfile ] || exit 1
[ -f entrypoint.sh ] || exit 1
[ -f sjgms.deb ] || exit 1

echo "Building docker image"
docker system prune -f
docker rmi $REPOTAG > /dev/null 2>&1
docker build --no-cache -t $REPOTAG .
if [ $? -ne 0 ]; then
  sleep 80
  docker build --no-cache -t $REPOTAG . || exit 1
fi

echo "Publishing docker image"
docker login || exit 1
docker push $REPOTAG || exit 1

echo "Done docker build process"
exit 0
