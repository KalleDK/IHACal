#!/usr/bin/env bash
echo "# IHA Calendars" > Readme.md
echo "Course | Feed | Html" >> Readme.md
echo "-------|------|-----" >> Readme.md
while read line
do
	./update.py $line
	curl -T --user $2:$3 calendars/$line.ics http://icalx.com/public/KalleDK/ > /dev/null 2>&1
	echo "$line | [![ICS](https://img.shields.io/badge/ICS-build-green.svg)](http://icalx.com/public/KalleDK/$line.ics) | [![HTML](https://img.shields.io/badge/HTML-build-green.svg)](http://www.icalx.com/html/KalleDK/week.php?cal=$line)" >> Readme.md
done < $1
echo "" >> Readme.md
echo "Kalle DK" >> Readme.md
