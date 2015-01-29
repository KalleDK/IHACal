#!/usr/bin/env bash
while read line
do
	./update.py $line
done < $1
