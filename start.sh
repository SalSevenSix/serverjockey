#!/bin/bash

wait_file() {
    local file="$1"
    shift
    local wait_seconds="${1:-10}"
    shift
    until [ -f "$file" ]; do
        if [ "$wait_seconds" -eq 0 ]; then
            echo "Timeout waiting for file: $file"
            exit 1
        fi
        sleep 1
        ((wait_seconds = wait_seconds - 1))
    done
}

check_dependencies() {
    echo
    echo "Checking dependencies..."
    echo
    echo "Checking for steamcmd."
    steamcmd +quit
    if [ $? -ne 0 ]; then
        echo "Steamcmd not found. Install commands;"
        echo "$ sudo add-apt-repository multiverse"
        echo "$ sudo dpkg --add-architecture i386"
        echo "$ sudo apt update"
        echo "$ sudo apt install lib32gcc1 steamcmd"
        exit 1
    fi

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
    echo "Checking for DISCORD_CONF."
    if [ ! -f "$DISCORD_CONF" ]; then
        {
            echo "{"
            echo "  \"BOT_TOKEN\": \"YOUR DISCORD LOGIN TOKEN HERE\","
            echo "  \"EVENTS_CHANNEL_ID\": \"YOUR DISCORD CHANNEL ID HERE\""
            echo "}"
        } >"$DISCORD_CONF"
        echo "Discord configuration file not found. A template has been created."
        echo "You need to edit this file to provide details about your Discord bot and server."
        echo "$ nano $DISCORD_CONF"
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
    echo "Installing serverjockey module dependencies."
    cd "$JOCKEY_DIR" || exit 1
    python3 -m pipenv install || exit 1

    echo
    echo "All dependencies installed. Creating a file to skip these checks;"
    date > "$DEPENDENCIES_FILE"
    echo "   $DEPENDENCIES_FILE"
    echo
}


echo "Paths init..."
cd $(dirname $0) || exit 1
JOCKEY_DIR="$(pwd)"
cd "$JOCKEY_DIR/.." || exit 1
HOME_DIR="$(pwd)"
DEPENDENCIES_FILE="$JOCKEY_DIR/dependencies.ok"
JOCKEY_LOG="$JOCKEY_DIR/serverjockey.log"
DISCORD_DIR="$JOCKEY_DIR/client/discord"
DISCORD_CONF="$JOCKEY_DIR/serverlink.json"
DISCORD_LOG="$JOCKEY_DIR/serverlink.log"
CLIENT_CONF="$JOCKEY_DIR/serverjockey-client.json"
rm "$CLIENT_CONF" >/dev/null 2>&1
if [ ! -f "$DEPENDENCIES_FILE" ]; then
    check_dependencies
fi

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


echo "Starting serverjockey webservice..."
cd "$JOCKEY_DIR" || exit 1
python3 -m pipenv run ./main.py --logfile "$JOCKEY_LOG" --clientfile "$CLIENT_CONF" --host "$HOST" --port "$PORT" "$MODULE" "$HOME_DIR" "$EXECUTABLE" >/dev/null 2>&1 &
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting serverjockey"

echo "Starting serverlink discord bot..."
cd "$DISCORD_DIR" || exit 1
wait_file "$CLIENT_CONF" 5 || exit 1
node index.js "$DISCORD_CONF" "$CLIENT_CONF" >"$DISCORD_LOG" 2>&1 &
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting serverlink"

exit 0
