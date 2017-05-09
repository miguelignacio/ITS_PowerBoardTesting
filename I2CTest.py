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
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from definitions import OpenFtdi
from definitions import CloseFtdi
#------------------------------------------ Main ----------------------------------------

def I2C():
 # Define I2C link address
 I2CLink         = 0xA
 print "-------------------------- Test I2C ------------------------------\n"
 OpenFtdi()
 #print "Raise threshold - Master"
 #WriteToDevice(I2CLink, 0x31, 0x3F, 0xFF, 0xFF) #raising threshold 
 #WriteToDevice(I2CLink, 0x33, 0x3F, 0xFF, 0xFF) 

 #print "Raise threshold - Slave"
 #WriteToDevice(I2CLink, 0x43, 0x3F, 0xFF, 0xFF) 
 #WriteToDevice(I2CLink, 0x51, 0x3F, 0xFF, 0xFF) 

 #print "---- LU enable ----"
 #print "Read Master LU State:  %X" %(ReadFromDevice(I2CLink, 0x20, 1))

 #print "Enable Master"
 #WriteToDevice(I2CLink, 0x20, 0x00)
 #WriteToDevice(I2CLink, 0x20, 0xFF)

 
 print "---- POT ----"
 print "Write: 0x34 0x35 0x36 0x37"
 WriteToDevice( I2CLink, 0x2c, 0x00, 0x59)
 WriteToDevice( I2CLink,0x2c, 0x01, 0x35)
 WriteToDevice( I2CLink,0x2c, 0x02, 0x36)
 WriteToDevice( I2CLink, 0x2c, 0x03, 0x37)
 l = ReadRSFromDevice( I2CLink, 0x2c, 1, 0x00)
 print "Read:"
 print l
 print [hex(int(x)) for x in l]

 print "Write: 0x44 0x45 0x46 0x47"
 WriteToDevice(I2CLink, 0x2d, 0x00, 0x44)
 WriteToDevice(I2CLink, 0x2d, 0x01, 0x45)
 WriteToDevice(I2CLink, 0x2d, 0x02, 0x46)
 WriteToDevice(I2CLink,0x2d, 0x03, 0x47)
 l = ReadRSFromDevice(I2CLink, 0x2d, 1, 0x00)
 print "Read:"
 print [hex(int(x)) for x in l]
 
 print 'This is the end of the I2C addresability test'
 CloseFtdi() # Ends communication with RDO board
 return 0


#print 'hello'
#I2C()

