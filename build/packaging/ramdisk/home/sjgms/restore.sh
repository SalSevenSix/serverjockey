#!/bin/bash

SOURCE=$1
MIRROR=$2
[ $(ls $SOURCE | wc -l) -eq 0 ] || exit 1
[ $(ls $MIRROR | wc -l) -eq 0 ] && exit 0
cp -r $MIRROR/* $SOURCE
exit $?
