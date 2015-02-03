#!/usr/bin/env bash
if [ "x${TRAVIS_PULL_REQUEST}" != "xfalse" ]
then
	./IHAcal.py --fetch --update --single IKT3
else
	./IHAcal.py --fetch --update --all
fi

cd courses
for f in *.ics
do
	echo "Processing $f file.."
	curl --user $1:$2 -T $f http://icalx.com/public/KalleDK/ > /dev/null 2>&1
done
