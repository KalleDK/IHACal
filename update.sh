#!/usr/bin/env bash
cd data
for f in *.ics
do
	echo "Processing $f file.."
	curl --user $1:$2 -T $f http://icalx.com/public/KalleDK/ > /dev/null 2>&1
done
