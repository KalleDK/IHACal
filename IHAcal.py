#!/usr/bin/env python

from __future__ import print_function

import os, sys, pytz, urllib2, urllib, re, time, pickle, argparse, ConfigParser

from icalendar import Calendar, Event, Timezone
from time import mktime
from datetime import datetime, timedelta

def filename(course):
	return re.sub('[^0-9a-zA-Z-_]+', '_', course)

def create_cal(name, desc):
	cal = Calendar()
	cal.add('version','2.0')
	cal.add('X-WR-CALNAME', name)
	cal.add('X-WR-CALDESC', desc)
	cal.add('X-PUBLISHED-TTL','PT8H')
	cal.add('CALSCALE','GREGORIAN')
	cal.add('METHOD','PUBLISH')
	cal.add_component(timezone)
	return cal

def create_time(year, week, weekday, hour, minute):
	if (weekday == 7):
		weekday = 0
	week = week - 1
	time_str = "{} {} {} {} {}".format(year, week, weekday, hour, minute)
	return datetime.fromtimestamp(mktime(time.strptime(time_str, '%Y %W %w %H %M'))).replace(tzinfo=pytz.timezone("Europe/Copenhagen"))

def save_course_pkl(course, subjects):
	subjects_array = []
	for subject in subjects:
		subjects_array.append(subject)
	output = open('pkl/{}.pkl'.format(filename(course)), 'wb')
	pickle.dump(subjects_array, output)
	output.close()

def load_course_pkl(course):
	pkl_file = open('pkl/{}.pkl'.format(filename(course)), 'rb')
	subjects = pickle.load(pkl_file)
	pkl_file.close()
	return subjects

def save_events(subjects):
	for subject in subjects:
		f = open('events/{}.ics'.format(filename(subject)),'wb')
		f.write(subjects[subject].to_ical())
		f.close()

def read_config(filename):
	config = ConfigParser.RawConfigParser()
	config.read(filename)
	return config

def read_args():
	parser = argparse.ArgumentParser()
	parser.add_argument ("--fetch",		action="store_true",	help="Update All Courses")
	parser.add_argument ("--update",	action="store_true",	help="Update All Courses")
	parser.add_argument ("--single",	action="store",		help="Specific Course")
	parser.add_argument ("--all",		action="store_true",	help="Update All Courses")
	parser.add_argument ("--courses",	action="store_true",    help="Update All Courses")
	return parser.parse_args()

def parse_week(subjects, f, year, week):
	weekday = 0
	event_state = 0
	subject = ''
	for line in f:
		if re.search("C0C0C0'>(.*)<", line):
			weekday = weekday + 1

		if (event_state == 0 and re.search("START OBJECT-CELL", line)):
			event_state = 1
			event = Event()

		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)(,.*)?<", line)
		if (event_state == 1 and match):
			event_state = 2
			event.add('dtstart', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(\d+):(\d+)(,.*)?<", line)
		if (event_state == 2 and match):
			event_state = 3
			event.add('dtend', create_time(year, week, weekday, int(match.group(1)), int(match.group(2))))

		match = re.search("<td align='center' bgcolor='#FFFFFF'><font color='#008000'>(.*)</font>", line)
		if (event_state == 3 and match):
			event_state = 4
			event.add('summary', match.group(1))
			subject = match.group(1)

		match = re.search("<td align='left' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 4 and match):
			event_state = 5
			event.add('location', match.group(1))

		match = re.search("<td align='right' bgcolor='#FFFFFF'><font color='#000080'>(.*)</font>", line)
		if (event_state == 5 and match):
			event_state = 6
			event.add('description', match.group(1))

		if re.search("END OBJECT-CELL", line):
			event_state = 0
			if subject not in subjects:
				subjects[subject] = Calendar()

			subjects[subject].add_component(event)

	
def fetch_course(course):
	global config
	global courses
	subjects = {}
	print('Fetching {}'.format(course))
	for week in range(config.getint('General','first_week'), config.getint('General','last_week')+1):
		
		# Progress numbers
		if (week - config.getint('General','first_week')) % 10 == 0:
			print('  ', end='')
		print("{:02d} ".format(week), end='')
		if (week - config.getint('General','first_week') + 1) % 10 == 0:
			 print('')
		sys.stdout.flush()

		#Fetch a week
		url = config.get('General','url')
		encoded = urllib.quote_plus(course)
		try: f = urllib2.urlopen(url.format(encoded,week))
		except IOError as e:
			print("Error")
			return 1

		#Parse week
		parse_week(subjects, f, config.getint('General','year'), week)
		f.close()

	print('')
	print('Subjects found')
	for subject in subjects:
		print(subject)
		sub_cal = Calendar()
		temp_event = Event()
		
		for event in subjects[subject].walk('VEVENT'):
			if 'dtstart' not in temp_event:
				temp_event = event
				continue

			if event.decoded('dtstart') - temp_event.decoded('dtend') < timedelta(0, 901) and temp_event.decoded('location') == event.decoded('location'):
				temp_event['dtend'] = event['dtend']
			else:
				sub_cal.add_component(temp_event)
				temp_event = event
			
		sub_cal.add_component(temp_event)
		subjects[subject] = sub_cal

	save_events(subjects)
	save_course_pkl(course, subjects)

def fetch_all_courses():
	global courses
	for course in courses:
		fetch_course(course)

def update_all_courses():
	global courses
	for course in courses:
		update_course_ics(course)

def update_course_ics(course):
	global courses
	subjects = load_course_pkl(course)
	cal = create_cal(courses[course], 'Calendar for {} at IHA'.format(courses[course]))
	for subject in subjects:
		f = open('events/{}.ics'.format(filename(subject)),'rb')
		content = f.read()
		sub_cal = Calendar().from_ical(content)
		f.close()
		for event in sub_cal.walk('VEVENT'):
			cal.add_component(event)

	f = open('courses/{}.ics'.format(filename(course)),'wb')
	f.write(cal.to_ical())
	f.close()

def fetch_courses_index():
	url = 'http://ase-timeplaner.au.dk/Scientia/SWS/semesterskema.html'
	state = 0
	courses = {}
	f = urllib2.urlopen(url)

	for line in f:
		match = re.search('<OPTION VALUE="(.+)">(.*)</OPTION>', line)
		if (state == 1 and match):
			if match.group(2) != '':
				courses[match.group(1)] = match.group(2)
		else:
			state = 0

		if re.search('<td><select size="5" name="lokale">', line):
			state = 1

	with open('courses.pkl', 'wb') as f:
		pickle.dump(courses, f, 0)

		

config = read_config('settings.cfg')
ns = read_args()
courses = pickle.load(open("courses.pkl", "rb"))
f = open('timezone.ics', 'rb')
timezone = Timezone.from_ical(f.read())
f.close()

if ns.fetch:
	if ns.single:
		fetch_course(ns.single)

	if ns.all:
		fetch_all_courses()

	if ns.courses:
		fetch_courses_index()

if ns.update:
	if ns.single:
		update_course_ics(ns.single)

	if ns.all:
		update_all_courses()
