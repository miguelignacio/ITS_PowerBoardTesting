#!/usr/bin/python

#----------------------------------------------------------------------------------------
# Title: Template test script for the ALICE ITS Power Board 8-module version
# Institution: Lawrence Berkeley National Laboratory
# Author: Alberto Collu
# Created: 11-09-2016
# Last edited: 11-09-2016 (Alberto Collu)
# Description: This script is used to generate I2C write and read commands for the ITS power board 8-channel
#----------------------------------------------------------------------------------------

import os
import io
import sys
import time
from definitions import *
from UsefulFunctions import *
#------------------------------------------ Main ----------------------------------------
ADCaddress = (0x21, 0x23, 0x22, 0x24)
POTaddress = (0x2C, 0x2D, 0x2E, 0x2F) #the first two are for master board, the latter for slave. Each one controls 4 channels.
THaddress = (0x31, 0x33, 0x43, 0x51) #pot addresses
IOaddress = (0x20, 0x26) #addresses of the IO modules that enable channels.

def I2C():
 # Define I2C link address
 print "-------------------------- Test I2C ------------------------------\n"
 OpenFtdi()
 print "Raising threshold"
 RaiseThresholdsToMax()

 print "---- Latch status----"
 print GetLatchStatus()

 print "---- Enabling all----"
 UnlatchAll()

 print "Reading ADCs"
 AddressConfigRegADC()
 I, V , I_ADC, V_ADC = ReadADC()
 print 'Current' , I
 print 'Voltage' , V

 print "Writing to POTS"
 WriteToDevice( I2CLink(), POTaddress[0], 0x00, 0x34)
 WriteToDevice( I2CLink(), POTaddress[0], 0x01, 0x35)
 WriteToDevice( I2CLink(), POTaddress[0], 0x02, 0x36)
 WriteToDevice( I2CLink(), POTaddress[0], 0x03, 0x37)
 print "Reading from POTS "
 l = ReadRSFromDevice( I2CLink(), POTaddress[0], 4, 0x00)
 print [hex(int(x)) for x in l]

 print "Writing to POTS" 
 WriteToDevice(I2CLink(), POTaddress[1], 0x00, 0x44)
 WriteToDevice(I2CLink(), POTaddress[1], 0x01, 0x45)
 WriteToDevice(I2CLink(), POTaddress[1], 0x02, 0x46)
 WriteToDevice(I2CLink(), POTaddress[1], 0x03, 0x47)
 print "Reading from POTS "
 l = ReadRSFromDevice(I2CLink(), POTaddress[0], 4, 0x00)
 print [hex(int(x)) for x in l]
 

 #print "Writing to POTS"
 #WriteToDevice( I2CLink(), POTaddress[2], 0x00, 0x34)
 #WriteToDevice( I2CLink(), POTaddress[2], 0x01, 0x35)
 #WriteToDevice( I2CLink(), POTaddress[2], 0x02, 0x36)
 #WriteToDevice( I2CLink(), POTaddress[2], 0x03, 0x37)
 #print "Reading from POTS "
 #l = ReadRSFromDevice( I2CLink(), POTaddress[2], 4, 0x00)
 #print [hex(int(x)) for x in l]

 #print "Writing to POTS" 
 #WriteToDevice(I2CLink(), POTaddress[3], 0x00, 0x44)
 #WriteToDevice(I2CLink(), POTaddress[3], 0x01, 0x45)
 #WriteToDevice(I2CLink(), POTaddress[3], 0x02, 0x46)
 #WriteToDevice(I2CLink(), POTaddress[3], 0x03, 0x47)
 #print "Reading from POTS "
 #l = ReadRSFromDevice(I2CLink(), POTaddress[3], 4, 0x00)
 #print [hex(int(x)) for x in l]


 print "Lowering thresholds"
 PowerThresholdsToMin()


 print 'This is the end of the I2C addresability test'
 CloseFtdi() # Ends communication with RDO board
 return 0


#print 'hello'
#I2C()

