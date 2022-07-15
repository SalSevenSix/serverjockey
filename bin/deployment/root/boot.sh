#!/bin/bash

TOKEN_FILE="/tmp/token.text"
wait_seconds=20
sleep 1
until [ -f "$TOKEN_FILE" ]; do
  [ $wait_seconds -eq 0 ] && exit 1
  sleep 1
  ((wait_seconds = wait_seconds - 1))
done
sleep 1

TOKEN="$(cat $TOKEN_FILE)"
rm $TOKEN_FILE > /dev/null 2>&1
IPV4="$(hostname -I | awk {'print$1'})"
PORT="6164"

{
  echo
  echo
  echo " ==========================================================="
  echo " =                    WELCOME TO ZOMBOX                    ="
  echo " ==========================================================="
  echo
  echo " Open the webapp then login with the token."
  echo
  echo " Address   http://${IPV4}:${PORT}"
  echo " Token     ${TOKEN}"
  echo
} > /dev/tty1

exit 0
