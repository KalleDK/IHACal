#!/usr/bin/env bash
while read line
do
	./update.py $line
	curl -T calendars/$line.ics http://icalx.com/public/KalleDK/
done < $1
