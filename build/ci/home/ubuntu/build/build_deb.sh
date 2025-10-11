#!/bin/bash

echo "Initialising CI build process"
[ "$(whoami)" = "root" ] || exit 1
which wget > /dev/null || exit 1
which jq > /dev/null || exit 1
which gh > /dev/null || exit 1
which docker > /dev/null || exit 1

cd "$(dirname $0)" || exit 1
BUILD_DIR="$(pwd)"
BUILD_USER="$(pwd | tr '/' ' ' | awk '{print $2}')"
DIST_DIR="$BUILD_DIR/dist"
BUILD_OK_FILE="$DIST_DIR/sjgms/build.ok"
CI_OK_FILE="$BUILD_DIR/build_deb.ok"
WEB_DIR="/var/www/downloads"
[ -d "$WEB_DIR" ] || exit 1
BRANCH="develop"
REPO_URL="https://raw.githubusercontent.com/SalSevenSix/serverjockey/$BRANCH"
COMMIT_FILE="${BRANCH}-commit.url"
BRANCH_FILE="/tmp/${$}-${BRANCH}-info.json"

docker image inspect rpmbuilder > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "CI Build rpmbuilder docker image"
  rm -rf /tmp/rpmbuilder > /dev/null 2>&1
  mkdir -p /tmp/rpmbuilder || exit 1
  cd /tmp/rpmbuilder || exit 1
  cat <<'EOF' > Dockerfile
FROM fedora:40
RUN dnf -y install rpm-build python3-pip
RUN yum -y install which wget unzip
RUN python3 -m pip install pipenv
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID rpmgroup && useradd -u $UID -g rpmgroup -m -s /bin/bash rpmuser
USER rpmuser
WORKDIR /home/rpmuser
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="$PATH:/home/rpmuser/.bun/bin"
ENTRYPOINT ["bash"]
EOF
  docker build --build-arg UID=$(id -u $BUILD_USER) --build-arg GID=$(id -g $BUILD_USER) -t rpmbuilder . || exit 1
fi

echo "CI Checking"
cd $BUILD_DIR || exit 1
LAST_URL="none"
[ -f "$COMMIT_FILE" ] && LAST_URL="$(head -1 $COMMIT_FILE)"
echo "  last commit     $LAST_URL"
su - $BUILD_USER -c "gh api repos/SalSevenSix/serverjockey/branches/$BRANCH" > $BRANCH_FILE
[ $? -eq 0 ] || exit 1
CURRENT_URL="$(jq -r .commit.url $BRANCH_FILE)"
rm $BRANCH_FILE > /dev/null 2>&1
echo "  current commit  $CURRENT_URL"
if [ "$LAST_URL" = "$CURRENT_URL" ]; then
  echo "No new commit found NOT building"
  exit 0
fi

echo "CI Preparing"
rm $CI_OK_FILE > /dev/null 2>&1
echo $CURRENT_URL > $COMMIT_FILE
chown $BUILD_USER $COMMIT_FILE || exit 1
chgrp $BUILD_USER $COMMIT_FILE || exit 1
systemctl stop serverjockey > /dev/null 2>&1
rm build.sh > /dev/null 2>&1
wget -O build.sh $REPO_URL/build/build.sh || exit 1
chmod 755 build.sh || exit 1
chown $BUILD_USER build.sh || exit 1
chgrp $BUILD_USER build.sh || exit 1

for PKG in rpm deb; do
  echo "CI Building $PKG"
  cd $BUILD_DIR || exit 1
  [ "$PKG" = "deb" ] && su - $BUILD_USER -c "$BUILD_DIR/build.sh $BRANCH"
  [ "$PKG" = "rpm" ] && docker run -v ${BUILD_DIR}:/home/rpmuser/build rpmbuilder build/build.sh $BRANCH
  [ -f "$BUILD_OK_FILE" ] || exit 1
  TIMESTAMP="$(head -1 $BUILD_OK_FILE)"

  echo "CI Packaging $PKG"
  [ "$PKG" = "deb" ] && $BUILD_DIR/deb.sh || exit 1
  [ "$PKG" = "rpm" ] && docker run -v ${BUILD_DIR}:/home/rpmuser/build rpmbuilder build/rpm.sh || exit 1

  echo "CI Publishing $PKG"
  cd $DIST_DIR || exit 1
  PKG_FILE="$(ls *.${PKG} | tail -1)"
  TARGET_FILE="sjgms-${BRANCH}-${TIMESTAMP}.${PKG}"
  chown root $PKG_FILE || exit 1
  chgrp root $PKG_FILE || exit 1
  mv $PKG_FILE $WEB_DIR/$TARGET_FILE || exit 1
  cd $WEB_DIR || exit 1
  ln -fs "$TARGET_FILE" "sjgms-${BRANCH}-latest.${PKG}" || exit 1

  echo "CI Cleanup $PKG"
  rm -rf "$DIST_DIR" > /dev/null 2>&1
  KEEP_COUNT=6
  ls -t sjgms-${BRANCH}-*.${PKG} | while read file; do
    [ $KEEP_COUNT -gt 0 ] || rm $file
    ((KEEP_COUNT = KEEP_COUNT - 1))
  done
done

echo "CI Docker deb"
cd $BUILD_DIR || exit 1
rm -rf docker > /dev/null 2>&1
mkdir docker || exit 1
cd docker || exit 1
cp $WEB_DIR/$TARGET_FILE sjgms.deb || exit 1
wget -O Dockerfile $REPO_URL/build/docker/Dockerfile || exit 1
wget -O entrypoint.sh $REPO_URL/build/docker/entrypoint.sh || exit 1
wget -O build.sh $REPO_URL/build/docker/build.sh || exit 1
chmod 755 build.sh || exit 1
./build.sh $BRANCH || exit 1

echo "CI Upgrade deb"
cd $WEB_DIR || exit 1
apt -y remove sjgms || exit 1
apt -y install ./$TARGET_FILE || exit 1

echo "CI Finishing"
cd $BUILD_DIR || exit 1
echo $TIMESTAMP > $CI_OK_FILE
/usr/local/bin/serverjockey_cmd.pyz -t wait:20 -c emailtoken
docker system prune > /dev/null 2>&1

echo "CI Done build process"
exit 0
