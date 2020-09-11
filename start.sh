#!/bin/bash

wait_file() {
  local file="$1"; shift
  local wait_seconds="${1:-10}"; shift
  until [ -f "$file" ]; do
    if [ "$wait_seconds" -eq 0 ]; then
        echo "Timeout waiting for file: $file"
        exit 1
    fi
    sleep 1
    ((wait_seconds=wait_seconds-1))
  done
}


cd $(dirname $0)/.. || exit 1
HOME_DIR="$(pwd)"
JOCKEY_DIR="$HOME_DIR/serverjockey"
DISCORD_DIR="$JOCKEY_DIR/client/discord"
CLIENT_CONF="$JOCKEY_DIR/jockey-client.json"
DISCORD_LOG="$JOCKEY_DIR/commandlink.log"
export VIRTUAL_ENV="$JOCKEY_DIR/venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
rm "$CLIENT_CONF" > /dev/null 2>&1

EXECUTABLE="runtime/start-server.sh"
MODULE="projectzomboid"
HOST="pznewhope.duckdns.org"
PORT="6164"
MY_IP=$(curl -X GET -k -s 'https://ip6.seeip.org/')
HOST_IP=$(host "$HOST" | grep IPv6 | grep -oE '[^[:space:]]+$' | tr -d '\n')
if [ "$MY_IP" != "$HOST_IP" ]; then
  HOST="localhost"
fi


cd "$JOCKEY_DIR" || exit 1
python main.py --clientfile "$CLIENT_CONF" --host "$HOST" --port "$PORT" "$MODULE" "$HOME_DIR" "$EXECUTABLE" > /dev/null 2>&1 &
echo "JOCKEY PID $!"

cd "$DISCORD_DIR" || exit 1
wait_file "$CLIENT_CONF" 5 || exit 1
node index.js "$CLIENT_CONF" > "$DISCORD_LOG" 2>&1 &
echo "DISCORD PID $!"

exit 0
