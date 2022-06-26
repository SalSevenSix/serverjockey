#!/bin/bash

wait_file() {
    local file="$1"
    local wait_seconds=$2
    until [ -f "$file" ]; do
        if [ $wait_seconds -eq 0 ]; then
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

check_dependencies_common() {
    echo
    echo "  checking for steamcmd."
    $(find_steamcmd) +quit > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "ERROR Steamcmd not found."
        echo "If you have any installation issues, please consult the website;"
        echo "  https://developer.valvesoftware.com/wiki/SteamCMD"
        echo "For Ubuntu/Debian;"
        echo "  $ sudo add-apt-repository multiverse"
        echo "  $ sudo dpkg --add-architecture i386"
        echo "  $ sudo apt update"
        echo "  $ sudo apt install lib32gcc-s1 steamcmd"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install steamcmd"
        exit 1
    fi

    echo
    echo "  checking for python, version 3.10 or higher required."
    python3 --version
    if [ $? -ne 0 ]; then
        echo "ERROR Python3 not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install software-properties-common"
        echo "  $ sudo add-apt-repository ppa:deadsnakes/ppa"
        echo "  $ sudo apt install python3"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install python3"
        exit 1
    fi

    echo
    echo "  checking for net tools."
    netstat --version
    if [ $? -ne 0 ]; then
        echo "ERROR Net Tools not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install net-tools"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install net-tools"
        exit 1
    fi

    echo
    echo "  checking for json query."
    jq --version
    if [ $? -ne 0 ]; then
        echo "ERROR Json Query not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install jq"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install jq"
        exit 1
    fi

    echo
    echo "  checking for DISCORD_CONF."
    if [ ! -f "$DISCORD_CONF" ]; then
        {
            echo "{"
            echo "  \"CMD_PREFIX\": \"!\","
            echo "  \"BOT_TOKEN\": \"YOUR DISCORD LOGIN TOKEN HERE\","
            echo "  \"EVENTS_CHANNEL_ID\": \"YOUR DISCORD CHANNEL ID HERE\","
            echo "  \"WHITELIST_DM\": \"Welcome to our server. User: \${user} Pass: \${pass}\""
            echo "}"
        } > "$DISCORD_CONF"
        chmod 644 "$DISCORD_CONF"
        echo "ERROR Discord configuration file not found. A template has been created."
        echo "You need to edit this file to provide details about your Discord bot and server."
        echo "  $ nano $DISCORD_CONF"
        exit 1
    fi
}

check_dependencies_jockey() {
    echo
    echo "  checking for pip."
    python3 -m pip --version
    if [ $? -ne 0 ]; then
        echo "ERROR Pip not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install python3-pip"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install python3-pip"
        exit 1
    fi

    echo
    echo "  checking for pipenv."
    python3 -m pipenv --version
    if [ $? -ne 0 ]; then
        echo "  pipenv not found, installing now."
        python3 -m pip install --user pipenv
        if [ $? -ne 0 ]; then
            echo "ERROR Failed installing pipenv. Sorry."
            exit 1
        fi
    fi

    echo
    echo "  installing serverjockey module dependencies."
    cd "$JOCKEY_DIR" || exit 1
    python3 -m pipenv install || exit 1
}

check_dependencies_discord() {
    echo
    echo "  checking for npm."
    npm --version
    if [ $? -ne 0 ]; then
        echo "ERROR Npm not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install npm"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install npm"
        exit 1
    fi

    echo
    echo "  checking for nodejs."
    node --version
    if [ $? -ne 0 ]; then
        echo "ERROR Nodejs not found."
        echo "For Ubuntu/Debian;"
        echo "  $ sudo apt install nodejs"
        echo "For RedHat/CentOS;"
        echo "  $ sudo yum install nodejs"
        exit 1
    fi

    echo
    echo "  checking for serverlink module dependencies."
    if [ ! -d "$DISCORD_DIR/node_modules" ]; then
        echo "  dependencies not found, installing now."
        cd "$DISCORD_DIR" || exit 1
        npm ci || exit 1
    fi
}

check_dependencies() {
    echo
    echo "CHECKING dependencies."
    check_dependencies_common
    [ -f "$JOCKEY_EXE" ] || check_dependencies_jockey
    [ -f "$DISCORD_EXE" ] || check_dependencies_discord
    echo
    echo "  all dependencies installed, creating a file to skip these checks;"
    date > "$DEPENDENCIES_FILE"
    echo "  $DEPENDENCIES_FILE"
    echo
}


# MAIN

echo "INITIALISING."
INITIAL_DIR="$(pwd)"
cd "$(dirname $0)" || exit 1
JOCKEY_DIR="$(pwd)"
JOCKEY_EXE="$JOCKEY_DIR/serverjockey.pyz"
DISCORD_DIR="$JOCKEY_DIR/client/discord"
DISCORD_EXE="$JOCKEY_DIR/serverlink"
[ -f "$DISCORD_EXE" ] && DISCORD_DIR="$JOCKEY_DIR"
HOME_DIR="$JOCKEY_DIR"
HOST="localhost"
PORT="6164"

cd "$INITIAL_DIR" || exit 1
for i in "$@"; do
    case $i in
        -d=*|--home=*)
        HOME_DIR="${i#*=}"
        cd "$HOME_DIR" || exit 1
        HOME_DIR="$(pwd)"
        shift
        ;;
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

if [ $(netstat --tcp --listen --numeric-ports | grep ":$PORT " | wc -l) -gt 0 ]; then
    echo "ERROR Port $PORT is already being listened."
    exit 1
fi

cd "$HOME_DIR" || exit 1
DISCORD_CONF="$HOME_DIR/serverlink.json"
CLIENT_CONF="$HOME_DIR/serverjockey-client.json"

echo "  home dir      $HOME_DIR"
echo "  jockey dir    $JOCKEY_DIR"
echo "  jockey exe    $([ -f $JOCKEY_EXE ] || echo 'NOT ')FOUND"
echo "  discord dir   $DISCORD_DIR"
echo "  discord exe   $([ -f $DISCORD_EXE ] || echo 'NOT ')FOUND"
echo "  discord conf  $DISCORD_CONF"
echo "  client conf   $CLIENT_CONF"
echo "  host:port     $HOST:$PORT"

DEPENDENCIES_FILE="$HOME_DIR/dependencies.ok"
[ -f "$DEPENDENCIES_FILE" ] || check_dependencies

jq . $DISCORD_CONF > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR Invalid JSON in $DISCORD_CONF"
    exit 1
fi


echo "STARTING ServerJockey webservice."
rm $CLIENT_CONF > /dev/null 2>&1
cd "$JOCKEY_DIR" || exit 1
if [ -f "$JOCKEY_EXE" ]; then
    $JOCKEY_EXE --host "$HOST" --port "$PORT" \
        --logfile "$HOME_DIR/serverjockey.log" --clientfile "$CLIENT_CONF" \
        "$HOME_DIR" > /dev/null 2>&1 &
else
    python3 -m pipenv run python3 -m core.system --host "$HOST" --port "$PORT" \
        --logfile "$HOME_DIR/serverjockey.log" --clientfile "$CLIENT_CONF" \
        "$HOME_DIR" > /dev/null 2>&1 &
fi
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting ServerJockey"

echo "STARTING ServerLink discord bot."
cd "$DISCORD_DIR" || exit 1
sleep 1
wait_file "$CLIENT_CONF" 5 || exit 1
if [ -f "$DISCORD_EXE" ]; then
    $DISCORD_EXE "$DISCORD_CONF" "$CLIENT_CONF" > "$HOME_DIR/serverlink.log" 2>&1 &
else
    node index.js "$DISCORD_CONF" "$CLIENT_CONF" > "$HOME_DIR/serverlink.log" 2>&1 &
fi
[ $? -eq 0 ] && ps -f -o pid,cmd -p $! | tail -1 || echo "Failed starting ServerLink"


exit 0
