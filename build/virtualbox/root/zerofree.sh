#!/bin/bash

echo "Starting zerofree process"
[ "$(whoami)" = "root" ] || exit 1
which zerofree > /dev/null || exit 1

echo " unmounting disk"
echo "u" > /proc/sysrq-trigger
echo " mount disk as readonly"
mount /dev/mapper / -o remount,ro
echo " running zerofree"
zerofree -v /dev/sda2

echo "Done"
echo " now shutdown 0"
echo " then compact disk and export ova"
exit 0
