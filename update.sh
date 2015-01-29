#!/usr/bin/env bash
echo "# IHA Calendars" > Readme.md
echo "[![Build Status](https://travis-ci.org/KalleDK/IHACal.svg?branch=master)](https://travis-ci.org/KalleDK/IHACal)" >> Readme.md
echo "" >> Readme.md
echo "Course | Feed | Html" >> Readme.md
echo "-------|------|-----" >> Readme.md
while read line
do
	./update.py $line
	curl --user $2:$3 -T calendars/$line.ics http://icalx.com/public/KalleDK/ > /dev/null 2>&1
	echo "$line | [![ICS](https://img.shields.io/badge/ICS-build-green.svg)](http://icalx.com/public/KalleDK/$line.ics) | [![HTML](https://img.shields.io/badge/HTML-build-green.svg)](http://www.icalx.com/html/KalleDK/week.php?cal=$line)" >> Readme.md
done < $1
echo "" >> Readme.md
echo "Kalle DK" >> Readme.md
