#!/usr/bin/env python

import os
from datetime import date, timedelta, datetime
from PowerboardTestDB import fillDBFromFiles

# set this to false to stop running the job
runJob = True
directory = "/home/its/Desktop/powerboard_8channel_tests/PB_8-channel/scripts/TXTFILES/"

if runJob:
	# find yesterday's date and format it correctly
	yesterdate = date.today() - timedelta(1)
	yesterday = yesterdate.strftime("%Y%m%d")

	# look for files starting with yesterday's date
	allFiles = os.listdir(directory)

	newFiles = []
	for file in allFiles:
		if file.startswith(yesterday):
			newFiles.append(file)

	# group files by timestamp
	testGroups = {}
	for file in newFiles:
		# get the timestamp
		timestamp = file.split("_")[0]
		# use it as the key in the dictionary of filenames
		# initialize the array if it doesn't already exist
		if timestamp not in testGroups:
			testGroups[timestamp] = []
		# add this file to the appropriate group
		testGroups[timestamp].append(file)

	# save each test group to the database
	for files in testGroups.itervalues():
		fillDBFromFiles(files, directory)

	print datetime.today(), "Files:", len(newFiles), "Groups: ", len(testGroups)
