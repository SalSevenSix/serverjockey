#!/bin/bash

cd "$(dirname $0)/client/cli" || exit 1
./serverjockey_cmd.py $@
exit $?
