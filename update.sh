#!/usr/bin/env bash
echo "# IHA Calendars" > Readme.md
echo "Course | Feed | Html" >> Readme.md
echo "--------------------" >> Readme.md
while read line
do
	#./update.py $line
	#curl -T calendars/$line.ics http://icalx.com/public/KalleDK/
	echo "$line | [![ICS](https://img.shields.io/badge/ICS-build-green.svg)](http://icalx.com/public/KalleDK/$line.ics) | [![HTML](https://img.shields.io/badge/HTML-build-green.svg)](http://icalx.com/public/KalleDK/$line)" >> Readme.md
done < $1
