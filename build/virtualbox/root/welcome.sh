#!/bin/bash

[ "$(whoami)" = "root" ] || exit 1
SJGMS_CLI="/usr/local/bin/serverjockey_cmd.pyz"
[ -f $SJGMS_CLI ] || exit 1

LOOP_RETRY=40
until [ "$(/sbin/runlevel)" = "N 5" ]; do
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 1 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

$SJGMS_CLI -n -t wait:20 -c welcome > /dev/tty1
exit $?
