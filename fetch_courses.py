#!/usr/bin/env python

import urllib
import re
from pprint import pprint
import pickle

url = 'http://ase-timeplaner.au.dk/Scientia/SWS/semesterskema.html'
state = 0
courses = {}
f = urllib.urlopen(url)

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
