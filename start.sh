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


echo "Checking dependencies..."
echo
echo "Checking for python. Python 3.8 or higher required."
python3 --version
if [ $? -ne 0 ]; then
   echo "Python3 not found. Install commands;"
   echo "$ sudo apt install software-properties-common"
   echo "$ sudo add-apt-repository ppa:deadsnakes/ppa"
   echo "$ sudo apt install python3"
   exit 1
fi

echo
echo "Checking for pip."
pip3 --version
if [ $? -ne 0 ]; then
   echo "Pip3 not found. Install command;"
   echo "$ sudo apt install python3-pip"
   exit 1
fi

echo
echo "Checking for pipenv."
python3 -m pipenv --version
if [ $? -ne 0 ]; then
   echo "Pipenv not found. Installing now."
   pip3 install --user pipenv
   if [ $? -ne 0 ]; then
      echo "Failed installing pipenv. Sorry."
      exit 1
   fi
fi

echo
echo "Checking for nodejs."
node --version
if [ $? -ne 0 ]; then
   echo "Nodejs not found. Install command;"
   echo "$ sudo apt install nodejs"
   exit 1
fi

echo
echo "Checking for npm."
npm --version
if [ $? -ne 0 ]; then
   echo "Npm not found. Install command;"
   echo "$ sudo apt install npm"
   exit 1
fi

echo
echo "Directory init..."
cd $(dirname $0) || exit 1
JOCKEY_DIR="$(pwd)"
cd "$JOCKEY_DIR/.." || exit 1
HOME_DIR="$(pwd)"
DISCORD_DIR="$JOCKEY_DIR/client/discord"
DISCORD_CONF="$JOCKEY_DIR/discord-bot.json"
DISCORD_LOG="$JOCKEY_DIR/serverlink.log"
CLIENT_CONF="$JOCKEY_DIR/jockey-client.json"
rm "$CLIENT_CONF" > /dev/null 2>&1

echo
echo "Checking for DISCORD_CONF."
if [ ! -f "$DISCORD_CONF" ]; then
   echo "Discord configuration file not found."
   echo "You need to create this file to hold the secret Discord Bot login token."
   echo "Use the following command, replacing YOUR TOKEN HERE with your token."
   echo "$ echo \"{ \\\"BOT_TOKEN\\\": \\\"YOUR TOKEN HERE\\\" }\" > $DISCORD_CONF"
   exit 1
fi

echo
echo "Checking for serverlink node_modules."
if [ ! -d "$DISCORD_DIR/node_modules" ]; then
   echo "Discord Bot package dependencies not found."
   echo "Installing discord.js, node-fetch."
   cd "$DISCORD_DIR" || exit 1
   npm install discord.js || exit 1
   npm install node-fetch || exit 1
fi

echo
echo "Environment init..."
EXECUTABLE="runtime/start-server.sh"
MODULE="projectzomboid"
HOST="pznewhope.duckdns.org"
PORT="6164"
MY_IP=$(curl -X GET -k -s 'https://ip6.seeip.org/')
HOST_IP=$(host "$HOST" | grep IPv6 | grep -oE '[^[:space:]]+$' | tr -d '\n')
if [ "$MY_IP" != "$HOST_IP" ]; then
  HOST="localhost"
fi


echo
echo "Starting serverjockey webservice..."
cd "$JOCKEY_DIR" || exit 1
python3 -m pipenv run ./main.py --clientfile "$CLIENT_CONF" --host "$HOST" --port "$PORT" "$MODULE" "$HOME_DIR" "$EXECUTABLE" > /dev/null 2>&1 &
[ $? -eq 0 ] && ps -fp $! || echo "Failed starting serverjockey"


echo
echo "Starting serverlink discord bot..."
cd "$DISCORD_DIR" || exit 1
wait_file "$CLIENT_CONF" 3 || exit 1
node index.js "$DISCORD_CONF" "$CLIENT_CONF" > "$DISCORD_LOG" 2>&1 &
[ $? -eq 0 ] && ps -fp $! || echo "Failed starting serverlink"

exit 0
