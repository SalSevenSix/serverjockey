#!/bin/bash

echo "Initialising release process"
[ "$(whoami)" = "root" ] || exit 1
[ -f /usr/local/bin/serverjockey_cmd.pyz ] || exit 1
which docker > /dev/null || exit 1
cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
WEB_DIR="/var/www/downloads"
DOCKER_IMAGE="salsevensix/serverjockey"
CI_OK_FILE="build_deb.ok"
[ -f $CI_OK_FILE ] || exit 1
TIMESTAMP="$(head -1 $CI_OK_FILE)"

echo "Confirming release"
cd $WEB_DIR || exit 1
SOURCE_FILE="sjgms-develop-${TIMESTAMP}.deb"
[ -f $SOURCE_FILE ] || exit 1
echo " source  deb : $SOURCE_FILE"
OSVER="ub$(grep 'VERSION_ID=' /etc/os-release | tr '"' ' ' | tr '.' ' ' | awk '{print $2}')"
VERSION="$(dpkg-deb -f $SOURCE_FILE Version)"
[ -z $VERSION ] && exit 1
RELEASE_FILE="sjgms-${VERSION}.${OSVER}.x86_64.deb"
[ -f $RELEASE_FILE ] && exit 1
echo " release deb : $RELEASE_FILE"
ZOMBOX_FILE="ZomBox-$(echo $TIMESTAMP | cut -c1-8).ova"
[ -f $ZOMBOX_FILE ] || exit 1
echo " zombox  ova : $ZOMBOX_FILE"
echo " source  img : ${DOCKER_IMAGE}:develop"
echo " release img : ${DOCKER_IMAGE}:${VERSION}"
RELEASE_EGG_FILE="egg-server-jockey-v$(echo $VERSION | tr '.' '-').json"
[ -f $RELEASE_EGG_FILE ] && exit 1
echo " release egg : $RELEASE_EGG_FILE"
read -p "press enter to continue"

echo "Docker image release"
cd $BUILD_DIR || exit 1
docker login || exit 1
docker image tag ${DOCKER_IMAGE}:develop ${DOCKER_IMAGE}:${VERSION} || exit 1
docker image tag ${DOCKER_IMAGE}:${VERSION} ${DOCKER_IMAGE}:latest || exit 1
docker push ${DOCKER_IMAGE}:${VERSION} || exit 1
docker push ${DOCKER_IMAGE}:latest || exit 1

echo "Pterodactyl egg release"
cd $WEB_DIR || exit 1
/usr/local/bin/serverjockey_cmd.pyz -nt pteroegg:$VERSION > $RELEASE_EGG_FILE || exit 1
chmod 644 $RELEASE_EGG_FILE || exit 1
ln -fs $RELEASE_EGG_FILE egg-server-jockey-latest.json || exit 1

echo "DEB package release"
cp $SOURCE_FILE $RELEASE_FILE || exit 1
chmod 644 $RELEASE_FILE || exit 1
ln -fs $RELEASE_FILE sjgms-master-latest.deb || exit 1

echo "ZomBox ova release"
chown root $ZOMBOX_FILE || exit 1
chgrp root $ZOMBOX_FILE || exit 1
chmod 644 $ZOMBOX_FILE || exit 1
ln -fs $ZOMBOX_FILE ZomBox-latest.ova || exit 1

echo "Done release process"
exit 0
