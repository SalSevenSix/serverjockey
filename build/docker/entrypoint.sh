#!/bin/bash

graceful_shutdown() {
  PID="$(ps -e -o pid,cmd | awk '/serverjockey\.pyz/{print $1}')"
  [ -z "$PID" ] && exit 0
  echo "Graceful shutdown, terminating $PID"
  kill $PID
  while ps -p $PID > /dev/null; do sleep 1; done
  exit 0
}

sleep 1
TZ=${TZ:-UTC}
export TZ
cd /home/container || exit 1
[ -d "serverlink" ] || mkdir serverlink
[ -f "serverlink/instance.json" ] || echo '{ "module": "serverlink", "hidden": true }' > serverlink/instance.json
[ -d ".local/share/Steam" ] || /usr/games/steamcmd +quit
[ -z "$STARTUP" ] && STARTUP="/usr/local/bin/serverjockey.pyz --noupnp --showtoken"
MODIFIED_STARTUP=$(echo ${STARTUP} | sed -e 's/{{/${/g' -e 's/}}/}/g')
echo -e ":/home/container$ ${MODIFIED_STARTUP}"
trap "graceful_shutdown" TERM INT
eval ${MODIFIED_STARTUP} &
WAIT_PID=$!
while read -r LINE; do
  [ "$LINE" = "shutdown" ] && graceful_shutdown
  eval /usr/local/bin/serverjockey_cmd.pyz -u container -c $LINE
done
wait $WAIT_PID
exit 0
