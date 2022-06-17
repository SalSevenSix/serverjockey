#!/bin/bash


foo=$(ps -u bsalis | grep node | awk {'print$1'})

[[ "$foo" == "" ]] || kill $foo

exit 0

