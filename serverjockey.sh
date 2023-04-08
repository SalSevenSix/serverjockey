#!/bin/bash

find_steamcmd() {
  /usr/games/steamcmd +quit >/dev/null 2>&1 && return 0
  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && return 0
  return 1
}

check_steamcmd() {
  echo
  echo "  checking for steamcmd."
  find_steamcmd
  if [ $? -ne 0 ]; then
    echo "ERROR Steamcmd not found."
    echo "If you have any installation issues, please consult the website;"
    echo "  https://developer.valvesoftware.com/wiki/SteamCMD"
    echo "For Ubuntu/Debian;"
    echo "  $ sudo apt install software-properties-common"
    echo "  $ sudo add-apt-repository multiverse"
    echo "  $ sudo dpkg --add-architecture i386"
    echo "  $ sudo apt update"
    echo "  $ sudo apt install lib32gcc-s1 steamcmd"
    echo "For RedHat/CentOS, follow instructions on the website for manual install."
    exit 1
  fi
}

check_jockey() {
  echo
  echo "  checking for python3, version 3.10 required."
  local python_check=$(which python3 | wc -l)
  [ $python_check -ne 0 ] && python_check=$(python3 --version | grep "Python 3\.10" | wc -l)
  if [ $python_check -eq 0 ]; then
    echo "ERROR Python3.10 not found."
    echo "For Ubuntu/Debian;"
    echo "  $ sudo apt install software-properties-common"
    echo "  $ sudo add-apt-repository ppa:deadsnakes/ppa"
    echo "  $ sudo apt install python3.10"
    echo "For RedHat/CentOS;"
    echo "  $ sudo yum install python3.10"
    exit 1
  fi

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
  python3 -m pipenv install
  if [ $? -ne 0 ]; then
    echo "ERROR Failed installing serverjockey dependencies. Sorry."
    exit 1
  fi
}

check_discord() {
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
  local discord_dir="$JOCKEY_DIR/client/discord"
  if [ ! -d "$discord_dir/node_modules" ]; then
    echo "  dependencies not found, installing now."
    cd $discord_dir || exit 1
    npm ci
    if [ $? -ne 0 ]; then
      echo "ERROR Failed installing serverlink dependencies. Sorry."
      exit 1
    fi
  fi

  echo
  echo "  checking for serverlink instance."
  local serverlink_dir="$HOME_DIR/serverlink"
  if [ ! -d "$serverlink_dir" ]; then
    echo "  instance not found, creating it now."
    mkdir -p $serverlink_dir
    cd $serverlink_dir || exit 1
    ln -s "$discord_dir/index.js" "index.js"
    echo '{ "module": "serverlink", "auto": "daemon", "hidden": true }' > instance.json
  fi
}

check_webapp() {
  echo
  echo "  checking for webapp."
  if [ ! -d "$JOCKEY_DIR/web" ]; then
    echo "  webapp not found, building it now."
    $JOCKEY_DIR/client/web/build.sh
  fi
}

check_dependencies() {
  echo
  echo "CHECKING dependencies."
  cd $JOCKEY_DIR || exit 1
  check_jockey
  check_discord
  check_webapp
  check_steamcmd
  echo
  echo "  all dependencies installed, creating a file to skip these checks;"
  date > "$DEPENDENCIES_FILE"
  echo "  $DEPENDENCIES_FILE"
  echo
}


# MAIN

INITIAL_DIR="$(pwd)"
cd "$(dirname $0)" || exit 1
JOCKEY_DIR="$(pwd)"
cd $INITIAL_DIR || exit 1
PARAMS=""

for i in "$@"; do
  case $i in
    --home=*)
      HOME_DIR="${i#*=}"
      cd $HOME_DIR || exit 1
      HOME_DIR="$(pwd)"
      PARAMS="$PARAMS --home $HOME_DIR"
    ;;
    --home)
      HOME_DIR="${i}"
    ;;
    *)
      if [ "$HOME_DIR" = "--home" ]; then
        HOME_DIR="${i}"
        cd $HOME_DIR || exit 1
        HOME_DIR="$(pwd)"
        PARAMS="$PARAMS --home $HOME_DIR"
      else
        PARAMS="$PARAMS ${i}"
      fi
    ;;
  esac
done

PARAMS="$(echo -e "${PARAMS}" | sed -e 's/^[[:space:]]*//')"
if [ -z $HOME_DIR ]; then
  HOME_DIR="$INITIAL_DIR"
  PARAMS="--home $HOME_DIR $PARAMS"
fi
DEPENDENCIES_FILE="$HOME_DIR/dependencies.ok"
[ -f $DEPENDENCIES_FILE ] || check_dependencies

cd $JOCKEY_DIR || exit 1
python3 -m pipenv run python3 -m core.system $PARAMS
exit $?
