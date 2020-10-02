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

find_steamcmd() {
  steamcmd +quit >/dev/null 2>&1 && echo steamcmd && return 0
  steamcmd.sh +quit >/dev/null 2>&1 && echo steamcmd.sh && return 0
  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0
  echo steamcmd && return 1
}

check_dependencies() {
    echo
    echo "Checking dependencies..."

    echo
    echo "Checking for steamcmd."
    $STEAMCMD +quit >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Steamcmd not found."
        echo "If you have any installation issues, please consult the website;"
        echo "  https://developer.valvesoftware.com/wiki/SteamCMD"
        echo "For Ubuntu/Debian;"
        echo "  $ sudo add-apt-repository multiverse"
        echo "  $ sudo dpkg --add-architecture i386"
        echo "  $ sudo apt update"
        echo "  $ sudo apt install lib32gcc1 steamcmd"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install steamcmd"
        exit 1
    fi

    echo
    echo "Checking for python. Python 3.8 or higher required."
    python3 --version
    if [ $? -ne 0 ]; then
        echo "Python3 not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install software-properties-common"
        echo "  $ sudo add-apt-repository ppa:deadsnakes/ppa"
        echo "  $ sudo apt install python3"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install python3"
        exit 1
    fi

    echo
    echo "Checking for pip."
    python3 -m pip --version
    if [ $? -ne 0 ]; then
        echo "Pip not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install python3-pip"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install python3-pip"
        exit 1
    fi

    echo
    echo "Checking for pipenv."
    python3 -m pipenv --version
    if [ $? -ne 0 ]; then
        echo "Pipenv not found. Installing now."
        python3 -m pip install --user pipenv
        if [ $? -ne 0 ]; then
            echo "Failed installing pipenv. Sorry."
            exit 1
        fi
    fi

    echo
    echo "Checking for npm."
    npm --version
    if [ $? -ne 0 ]; then
        echo "Npm not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install npm"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install npm"
        exit 1
    fi

    echo
    echo "Checking for nodejs."
    node --version
    if [ $? -ne 0 ]; then
        # TODO use npm to install it instead
        echo "Nodejs not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install nodejs"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install nodejs"
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
        echo "  $ nano $DISCORD_CONF"
        exit 1
    fi

    echo
    echo "Checking for serverlink node_modules."
    if [ ! -d "$DISCORD_DIR/node_modules" ]; then
        # TODO Get this to to install needed packages from package-lock.json
        echo "Discord Bot package dependencies not found. Installing dependencies."
        cd "$DISCORD_DIR" || exit 1
        npm install discord.js || exit 1
        npm install node-fetch || exit 1
    fi

    echo
    echo "Installing serverjockey module dependencies."
    cd "$JOCKEY_DIR" || exit 1
    python3 -m pipenv install || exit 1

    echo
    echo "All dependencies installed."
    echo "Creating a file to skip these checks;"
    date > "$DEPENDENCIES_FILE"
    echo "   $DEPENDENCIES_FILE"
    echo
}


echo "Paths init..."
cd "$(dirname $0)" || exit 1
JOCKEY_DIR="$(pwd)"
cd "$JOCKEY_DIR/.." || exit 1
HOME_DIR="$(pwd)/servers"
DEPENDENCIES_FILE="$JOCKEY_DIR/dependencies.ok"
JOCKEY_LOG="$JOCKEY_DIR/serverjockey.log"
DISCORD_DIR="$JOCKEY_DIR/client/discord"
DISCORD_CONF="$JOCKEY_DIR/serverlink.json"
DISCORD_LOG="$JOCKEY_DIR/serverlink.log"
CLIENT_CONF="$JOCKEY_DIR/serverjockey-client.json"
STEAMCMD=$(find_steamcmd)
rm "$CLIENT_CONF" >/dev/null 2>&1
if [ ! -f "$DEPENDENCIES_FILE" ]; then
    check_dependencies
fi

echo "Environment init..."
HOST="localhost"
PORT="6164"
for i in "$@"; do
    case $i in
        -h=*|--host=*)
        HOST="${i#*=}"
        shift
        ;;
        -p=*|--port=*)
        PORT="${i#*=}"
        shift
        ;;
        *)
        # unknown
        ;;
    esac
done
if [ "$HOST" != "localhost" ]; then
    my_ip=$(curl -s https://ip6.seeip.org)
    host_ip=$(host "$HOST" | grep IPv6 | grep -oE '[^[:space:]]+$' | tr -d '\n')
    if [ "$my_ip" != "$host_ip" ]; then
        echo "WARNING: host name provided does not match ip address, using localhost instead"
        HOST="localhost"
    fi
fi


echo "Starting serverjockey webservice..."
cd "$JOCKEY_DIR" || exit 1
python3 -m pipenv run python3 -m core.system --host "$HOST" --port "$PORT" --logfile "$JOCKEY_LOG" --clientfile "$CLIENT_CONF" "$HOME_DIR" >/dev/null 2>&1 &
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting serverjockey"

echo "Starting serverlink discord bot..."
cd "$DISCORD_DIR" || exit 1
wait_file "$CLIENT_CONF" 5 || exit 1
node index.js "$DISCORD_CONF" "$CLIENT_CONF" >"$DISCORD_LOG" 2>&1 &
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting serverlink"

exit 0
