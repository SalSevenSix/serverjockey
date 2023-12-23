#!/bin/bash

graceful_shutdown() {
  PID="$(ps -e -o pid,cmd | awk '/serverjockey\.pyz/{print $1}')"
  echo "Trapped shutdown signal, terminating $PID"
  kill $PID
}

setup_serverlink() {
  mkdir serverlink || exit 1
  echo '{ "module": "serverlink", "hidden": true }' > serverlink/instance.json
}

sleep 1
[ -z "$STARTUP" ] && STARTUP="/usr/local/bin/serverjockey.pyz --noupnp --dbfile --showtoken"
PATH="$PATH:/usr/games"
export PATH
TZ=${TZ:-UTC}
export TZ

cd /home/container || exit 1
[ -d "serverlink" ] || setup_serverlink
steamcmd +quit

MODIFIED_STARTUP=$(echo ${STARTUP} | sed -e 's/{{/${/g' -e 's/}}/}/g')
echo -e ":/home/container$ ${MODIFIED_STARTUP}"
trap 'graceful_shutdown' TERM INT
eval ${MODIFIED_STARTUP} &
WAIT_PID=$!
wait $WAIT_PID
trap - TERM INT
wait $WAIT_PID

exit 0
