#!/bin/bash

graceful_shutdown() {
  PID="$(ps -e -o pid,cmd | awk '/serverjockey\.pyz/{print $1}')"
  echo "Trapped shutdown signal, terminating $PID"
  kill $PID
  while ps -p $PID > /dev/null; do sleep 1; done
  exit 0
}

sleep 1
TZ=${TZ:-UTC}
export TZ
cd /home/container || exit 1
if [ ! -d "serverlink" ]; then
  mkdir serverlink || exit 1
  echo '{ "module": "serverlink", "hidden": true }' > serverlink/instance.json
  /usr/games/steamcmd +quit
fi

[ -z "$STARTUP" ] && STARTUP="/usr/local/bin/serverjockey.pyz --noupnp --showtoken"
MODIFIED_STARTUP=$(echo ${STARTUP} | sed -e 's/{{/${/g' -e 's/}}/}/g')
echo -e ":/home/container$ ${MODIFIED_STARTUP}"
trap "graceful_shutdown" TERM INT
eval ${MODIFIED_STARTUP} &
while read -r line; do
  [ "$line" = "shutdown" ] && break
  eval "/usr/local/bin/serverjockey_cmd.pyz -u container -c $line"
done
graceful_shutdown
