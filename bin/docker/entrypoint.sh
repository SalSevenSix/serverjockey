#!/bin/bash

setup_serverlink() {
  mkdir serverlink || exit 1
  echo "{ \"module\": \"serverlink\", \"auto\": \"daemon\", \"hidden\": true }" > serverlink/instance.json
  {
    echo "{"
    echo "  \"CMD_PREFIX\": \"!\","
    echo "  \"ADMIN_ROLE\": \"pzadmin\","
    echo "  \"BOT_TOKEN\": null,"
    echo "  \"EVENTS_CHANNEL_ID\": null,"
    echo "  \"WHITELIST_DM\": \"Welcome to our server.\nYour login is \${user} and password is \${pass}\""
    echo "}"
  } > serverlink/serverlink.json
}

sleep 1
PATH="$PATH:/usr/games"
export PATH
TZ=${TZ:-UTC}
export TZ

cd /home/container || exit 1
[ -d "serverlink" ] || setup_serverlink
steamcmd +quit

MODIFIED_STARTUP=$(echo ${STARTUP} | sed -e 's/{{/${/g' -e 's/}}/}/g')
echo -e ":/home/container$ ${MODIFIED_STARTUP}"
trap 'kill $PID' TERM INT
eval ${MODIFIED_STARTUP} &
WPID=$!
PID=$(ps -e -o pid,cmd | awk '/serverjockey\.pyz/{print $1}')
wait $WPID
trap - TERM INT
wait $WPID

exit 0
