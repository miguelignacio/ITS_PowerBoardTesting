#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "2.0"
__status__ = "Prototype"

from definitions import *
from UsefulFunctions import *

#################################################################
OpenFtdi() # Starts communication with RDO board

LowerThresholdsToMin() #to latch everything and erase whatever previous state
RaiseThresholdsToMax()
UnlatchAll()
print GetLatchStatus()
AddressConfigRegADC()
for i in range(8): SetVoltage(channel=i, voltage=100)
I, V, I_ADC, V_ADC = ReadADC()
print V

##an example of long stability test might be: 

##for n in range(1000):
    #I, V, I_ADC, V_ADC = ReadADC()
    #time.sleep(30) take data every 30 s.

CloseFtdi() # Ends communication with RDO board
#################################################################3


