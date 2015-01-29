#!/usr/bin/env python
from icalendar import Calendar, Event
from datetime import datetime
import time
from time import mktime
from datetime import datetime
import os
import sys
import pytz
import urllib
import re

last_week = 52
year = 2015
course = sys.argv[1]
url = "http://ase-timeplaner.au.dk:8080/Rapporterer/Individuel;Studieprogrammer;id;{}?&template=SWS_PRO_IND&weeks={}&days=1-5&periods=1-34"

cal = Calendar()
cal.add('version','2.0')
cal.add('X-WR-CALNAME', 'IHACal')
cal.add('X-WR-CALDESC', 'Kalender for IHA')

def create_time(year, week, weekday, hour, minute):
	if (weekday == 7):
		weekday = 0
	week = week - 1
	time_str = "{} {} {} {} {}".format(year, week, weekday, hour, minute)
	return datetime.fromtimestamp(mktime(time.strptime(time_str, '%Y %W %w %H %M'))).replace(tzinfo=pytz.timezone("Europe/Copenhagen"))


for week in range(1, last_week+1):
	weekday = 0
	event_state = 0
	f = urllib.urlopen(url.format(course, week))
	for line in f:
		if re.search("C0C0C0'>(.*)<", line):
			weekday = weekday + 1
			print "New Week"
			print weekday

		if (event_state == 0 and re.search("START OBJECT-CELL", line)):
			event_state = 1
			print "New Event"
			event = Event()
	
		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)<", line)
		if (event_state == 1 and match):
			event_state = 2
			print match.group(1)
			print match.group(2)
			event.add('dtstart', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)<", line)
		if (event_state == 2 and match):
			event_state = 3
			print match.group(1)
			print match.group(2)
			event.add('dtend', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='center' bgcolor='#FFFFFF'><font color='#008000'>(.*)</font>", line)
		if (event_state == 3 and match):
			event_state = 4
			print match.group(1)
			event.add('summary', match.group(1))

		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 4 and match):
			event_state = 5
			print match.group(1)
			event.add('location', match.group(1))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 5 and match):
			event_state = 6
			print match.group(1)

		if re.search("END OBJECT-CELL", line):
			print "End Event"
			event_state = 0
			cal.add_component(event)

f = open('calendars/{}.ics'.format(course),'wb')
f.write(cal.to_ical())
f.close()
