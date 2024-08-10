#!/bin/bash

[ "$(whoami)" = "root" ] || exit 1
SJGMS_CLI="/usr/local/bin/serverjockey_cmd.pyz"
[ -f $SJGMS_CLI ] || exit 1

LOOP_RETRY=30
until [ "$(/sbin/runlevel)" = "N 5" ]; do
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 1 && ((LOOP_RETRY = LOOP_RETRY - 1))
done
sleep 1

LOOP_RETRY=10
until $SJGMS_CLI -n; do
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 1 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

$SJGMS_CLI -nc welcome > /dev/tty1 || exit 1
exit 0
