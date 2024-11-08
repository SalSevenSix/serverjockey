#!/bin/bash

rm /tmp/welcome.sh.* > /dev/null 2>&1
NOTIFY_FILE="/tmp/welcome.sh.$$"
/usr/bin/inotifywait -t 80 /etc/issue > $NOTIFY_FILE 2>/dev/null &

SJGMS_CLI="/usr/local/bin/serverjockey_cmd.pyz"
[ -f $SJGMS_CLI ] || exit 1

LOOP_RETRY=60
until [ "$(/sbin/runlevel)" = "N 5" ] || [ "$(head -1 $NOTIFY_FILE)" = "/etc/issue OPEN " ]; do
  [ $LOOP_RETRY -eq 0 ] && exit 1
  sleep 1 && ((LOOP_RETRY = LOOP_RETRY - 1))
done

$SJGMS_CLI -n -t wait:20 -c welcome > /dev/tty1
exit $?
