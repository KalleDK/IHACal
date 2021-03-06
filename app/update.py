#!/usr/bin/env python
import json
import requests
from lxml import html
import os, sys
from datetime import datetime, timedelta
from icalendar import Calendar, Event as ICALEvent
import pytz
import re

tz = pytz.timezone("Europe/Copenhagen")
day_count = int(os.getenv('DAYCOUNT','1'))
username = os.environ['USERNAME']
password = os.environ['PASSWORD']

ics_url = 'http://icalx.com/public/KalleDK'

def makeBadge(name, url, status):
	badge = 'https://img.shields.io/badge/{}-view-{}.svg'.format(name, status)
	return '[![{}]({})]({})'.format(name,badge,url)

class Event:
	def __init__(self, xml_event, date):
		data = xml_event.xpath('table/tr/td/font')
		
		# Yes they do 12:00,12:00 sometimes... #¤%&
		time = data[0].text.split(',')[-1]
		self.starttime = date
		self.starttime = self.starttime.replace(second=0,microsecond=0)
		self.starttime = self.starttime.replace(hour=int(time.split(':')[0]))
		self.starttime = self.starttime.replace(minute=int(time.split(':')[1]))
		
		time = data[1].text.split(',')[-1]
		self.endtime = date
		self.endtime = self.endtime.replace(second=0,microsecond=0)
		self.endtime = self.endtime.replace(hour=int(time.split(':')[0]))
		self.endtime = self.endtime.replace(minute=int(time.split(':')[1]))
		
		self.course = data[2].text or ''
		self.location = data[3].text or ''
		self.instructor = data[4].text or ''
		
	def toICal(self):
		ical = ICALEvent()
		ical.add('dtstart',self.starttime)
		ical.add('dtend',self.endtime)
		ical.add('summary', self.course)
		ical.add('location', self.location)
		ical.add('description', self.instructor)
		return ical
		

class Timeplaner:

	# 20 min * 60 s/min
	smallbreak = timedelta(seconds=(20*60))

	def __init__(self):
		self.course_list_url = "http://ase-timeplaner.au.dk/Scientia/SWS/semesterskema.html"
		self.week_template_url = "http://ase-timeplaner.au.dk:8080/Rapporterer/Individuel;Studieprogrammer;id;{}?&template=SWS_PRO_IND&weeks={}&days=1-7&periods=1-34"
		self.session = requests.Session()
		self.course_list = self.getCourseList()
		self.cache = {}

	def downloadPage(self, url, root=True):
		request = self.session.get(url)
		if root:
			return html.fromstring(request.text)
		else:
			return request

	def getCourseList(self):
		root = self.downloadPage(self.course_list_url)	

		# Return the list of courses
		url = root.xpath('//select[@name="lokale"]/option/@value')
		names = root.xpath('//select[@name="lokale"]/option/text()')
		return zip(names,url)

	def getWeek(self, course, date):
		# Get week number from date
		( _, week, _ ) = datetime.isocalendar(date)
		if week > 52:
			week -= 52

		# Make weekid for cache identification
		weekid = course + str(week)

		# Download the individual page for that course and that week
		if not weekid in self.cache:
			self.cache[weekid] = self.downloadPage(self.week_template_url.format(course,week))
		
		# Return the table that actually contains the schedule
		return self.cache[weekid].xpath('/html/body/table[2]')[0]

	def getEventsFromDate(self, course, date):
		# Get weeks schedule
		week = self.getWeek(course, date)

		# Get day of week
		( _, _, day ) = datetime.isocalendar(date)
		
		# How many rows does the day span
		row_span = week.xpath('tr/td[1]//@rowspan')
		row_span = [int(x) for x in row_span]
		start_row = 2 + sum(row_span[:day-1])
		row_count = row_span[day-1]
		
		xml_events = []
		# Get the events from a specific day
		for row in range(0,row_count):
			# Get the events from a specific row
			xml_events += week.xpath('tr[' + str(start_row + row) + ']/td[table]')

		# Reverse so we can use pop and append from the end
		xml_events.reverse()

		# List of events
		events = []
		
		while xml_events:
			# Pick first event
			event = Event(xml_events.pop(), date)
			
			if xml_events:
				# Look at next event
				next_event = Event(xml_events[-1],date)
				
				# If next event is the same course as first event and it's only a small break
				if next_event.course == event.course and (next_event.starttime - event.endtime) < self.smallbreak:
					# Combine the two events
					event.endtime = next_event.endtime
					
					# Remove the next event from the queue
					xml_events.pop()
					
			# Push event to list
			events.append(event)
			
		return events

	def getCourseCalendar(self, course, start_date, day_count):
		cal    = Calendar()
		events = []
		
		cal.add('version','2.0')
		cal.add('X-WR-CALNAME', course[0])
		cal.add('X-WR-CALDESC', 'Calendar for {} at IHA'.format(course[0]))
		
		for date in (start_date + timedelta(n) for n in range(day_count)):
			print('.',end='')
			sys.stdout.flush()
			events += self.getEventsFromDate(course[1], date)
		print("\n")
		
		for event in events:
			cal.add_component(event.toICal())
		
		return cal

tp = Timeplaner()

courses = tp.getCourseList()

for course in courses:
	print("Course: " + course[0] + "\n")
	ics = tp.getCourseCalendar(course,datetime.now(tz), day_count).to_ical()
	r = requests.put(ics_url + "/" + course[0] + ".ics", auth=(username, password), data=ics)

courses = tp.getCourseList()
	
with open('README.md','wb') as f:
	f.write(bytes("# IHA Calendars\n",'UTF-8'))
	f.write(bytes("\n\n",'UTF-8'))
	f.write(bytes("Course | Feed | Html\n",'UTF-8'))
	f.write(bytes("-------|------|-----\n",'UTF-8'))
	for course in courses:
		course_name = course[0]
		ics_badge   = makeBadge('ICS','http://icalx.com/public/KalleDK/{}.ics'.format(course_name), 'green')
		html_badge  = makeBadge('HTML','http://cdn.instantcal.com/cvj.html?id=cv_nav5&file=http%3A%2F%2Ficalx.com%2Fpublic%2FKalleDK%2F{}.ics&theme=RE&ccolor=%23ffffc0&dims=1&gtype=cv_daygrid&gcloseable=0&gnavigable=1&gperiod=day5&itype=cv_simpleevent&width=800'.format(course_name), 'green')
		f.write(bytes("{} | {} | {}\n".format(course_name, ics_badge, html_badge),'UTF-8'))
		