#!/bin/bash

wait_seconds=30
until [ "$(/sbin/runlevel)" == "N 5" ]; do
  [ $wait_seconds -eq 0 ] && exit 1
  sleep 1
  ((wait_seconds = wait_seconds - 1))
done
sleep 1

wait_seconds=10
until /usr/local/bin/serverjockey_cmd.pyz -n; do
  [ $wait_seconds -eq 0 ] && exit 1
  sleep 1
  ((wait_seconds = wait_seconds - 1))
done

/usr/local/bin/serverjockey_cmd.pyz -nc welcome > /dev/tty1
exit $?
