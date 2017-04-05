#!/usr/bin/python

from __future__ import division
import os
import io
import sys
import time
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
import math
import datetime

ENaddress = (0x26, 0x25)
DACaddress = (0x32, 0x50)

def BiasScan(board,stepsize):
	POTaddress = (0x2C, 0x2D, 0x2E, 0x2F)

	#WriteToDevice(0x31, 0x3F, 0xFF, 0xFF) #raise thresholds to unlatch channels
	#WriteToDevice(0x33, 0x3F, 0xFF, 0xFF)

	#for p in range(0, 8, 1):
	#	WriteToDevice(int(POTaddress[board*2 + int(p/4)]), int(p%4), 0xB4)

	#WriteToDevice(0x20, 0x00) # Enable the Outputs
	#WriteToDevice(0x20, 0xFF) # Enable the Latch Read Back

	#WriteToDevice(0x26, 0x80) #enable bias Master
	#WriteToDevice(0x25, 0x80) #enable bias Slave
	WriteToDevice(int(ENaddress[board]), 0x80) #enable bias Slave

	for VAL in range(0, 255, int(stepsize)):
		print VAL
		time.sleep(1)
		#WriteToDevice(0x32, 0x3F, VAL, 0x00) #Master
		#WriteToDevice(0x50, 0x3F, VAL, 0x00) #Slave
		WriteToDevice(int(DACaddress[board]), 0x3F, VAL, 0x00)
		time.sleep(5)

	#WriteToDevice(0x32, 0x3F, 0xFF, 0x00) #Master
	#WriteToDevice(0x50, 0x3F, 0xFF, 0x00) #Slave
	WriteToDevice(int(DACaddress[board]), 0x3F, 0xFF, 0x00)
	time.sleep(5)

	#WriteToDevice(0x31, 0x3F, 0x00, 0x00) #lower thresholds to relatch
	#WriteToDevice(0x33, 0x3F, 0x00, 0x00)

	#WriteToDevice(0x25, 0xFF) #shutdown bias
	WriteToDevice(int(ENaddress[board]), 0xFF) #shutdown bias

	print "DONE"

	return 0
