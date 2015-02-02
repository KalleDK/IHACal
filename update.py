#!/usr/bin/env python

from __future__ import print_function

import os, sys, pytz, urllib, re, time, pickle, argparse

from icalendar import Calendar, Event
from time import mktime
from datetime import datetime

year = 2015
first_week = 1
last_week = 25
url = "http://ase-timeplaner.au.dk:8080/Rapporterer/Individuel;Studieprogrammer;id;{}?&template=SWS_PRO_IND&weeks={}&days=1-5&periods=1-34"
readme = 'data/README.md'

parser = argparse.ArgumentParser()
parser.add_argument ("--single",	action="store_true",      help="Only first course")
parser.add_argument ("--readme",	action="store_true",      help="Only first course")
ns = parser.parse_args()

courses = 0

def create_time(year, week, weekday, hour, minute):
	if (weekday == 7):
		weekday = 0
	week = week - 1
	time_str = "{} {} {} {} {}".format(year, week, weekday, hour, minute)
	return datetime.fromtimestamp(mktime(time.strptime(time_str, '%Y %W %w %H %M'))).replace(tzinfo=pytz.timezone("Europe/Copenhagen"))

def parse_week(cal, f, year, week):
	weekday = 0
	event_state = 0
	for line in f:
		if re.search("C0C0C0'>(.*)<", line):
			weekday = weekday + 1
			#print "New Week"
			#print weekday

		if (event_state == 0 and re.search("START OBJECT-CELL", line)):
			event_state = 1
			#print "New Event"
			event = Event()
	
		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)<", line)
		if (event_state == 1 and match):
			event_state = 2
			#print match.group(1)
			#print match.group(2)
			event.add('dtstart', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)<", line)
		if (event_state == 2 and match):
			event_state = 3
			#print match.group(1)
			#print match.group(2)
			event.add('dtend', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='center' bgcolor='#FFFFFF'><font color='#008000'>(.*)</font>", line)
		if (event_state == 3 and match):
			event_state = 4
			#print match.group(1)
			event.add('summary', match.group(1))

		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 4 and match):
			event_state = 5
			#print match.group(1)
			event.add('location', match.group(1))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 5 and match):
			event_state = 6
			event.add('description', match.group(1))
			#print match.group(1)

		if re.search("END OBJECT-CELL", line):
			#print "End Event"
			event_state = 0
			cal.add_component(event)

def save_cal(cal, course):
	print("\nSaving {}.ics\n".format(course))
	file_name = re.sub('[^0-9a-zA-Z]+', '_', course)
	f = open('data/{}.ics'.format(file_name),'wb')
	f.write(cal.to_ical())
	f.close()

def create_readme():
	f = open(readme, 'wb')
	f.write("# IHA Calendars\n")
	f.write("[![Build Status](https://travis-ci.org/KalleDK/IHACal.svg?branch=master)](https://travis-ci.org/KalleDK/IHACal)\n\n")
	f.write("Course | Feed | Html\n")
	f.write("-------|------|-----\n")
	f.close()

def append_readme(course, courses):
	file_name = re.sub('[^0-9a-zA-Z]+', '_', course)
	f = open(readme, 'a')
	f.write("{} | [![ICS](https://img.shields.io/badge/ICS-build-green.svg)](http://icalx.com/public/KalleDK/{}.ics) | [![HTML](https://img.shields.io/badge/HTML-build-green.svg)](http://www.icalx.com/html/KalleDK/week.php?cal={})\n".format(courses[course], file_name, file_name))
	f.close()

def make_readme():
	courses = pickle.load( open( "courses.pkl", "rb" ) )
	create_readme()
	for course in sorted(courses):
		append_readme(course, courses)
		
	
def main():
	courses = pickle.load( open( "courses.pkl", "rb" ) )
	for course in sorted(courses):
		cal = Calendar()
		cal.add('version','2.0')
		cal.add('X-WR-CALNAME', courses[course])
		cal.add('X-WR-CALDESC', 'Calendar for {} at IHA'.format(courses[course]))
		print('Fetching {}\'s weeks'.format(courses[course]))

		for week in range(first_week, last_week+1):
			if (week - first_week) % 10 == 0:
				print('  ', end='')
			print("{:02d} ".format(week), end='')
			if (week - first_week + 1) % 10 == 0:
				print('')
			sys.stdout.flush()
			try: 
				f = urllib.urlopen(url.format(course, week))
			except urllib.URLError, e:
				quit()
	
			parse_week(cal, f, year, week)
	
			f.close()
	
		save_cal(cal, course)
		if ns.single:
			sys.exit(0)

if ns.readme:
	make_readme()
else:
	main()
	make_readme()
