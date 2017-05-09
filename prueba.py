#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "2.0"
__status__ = "Prototype"


###work in progress###, 03/23/17
from definitions import OpenFtdi
from definitions import CloseFtdi
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from definitions import AppendDataBufferToFile

from UsefulFunctions import *
IOaddress = (0x20, 0x26)


OpenFtdi() # Starts communication with RDO board
LowerThresholdsToMin() #to latch everything and erase whatever previous state
RaiseThresholdsToMax()
for channel in range(8):
    print PrintLatchStatus()
    Unlatch(channel)
print PrintLatchStatus()
AddressConfigRegADC()

I, V, I_ADC, V_ADC = ReadADC()
print V

for i in range(8):
    SetVoltage(channel=i, voltage=100)

SetVoltage(channel=2, voltage=255)
time.sleep(0.02)
I, V, I_ADC, V_ADC = ReadADC()
print I,V,I_ADC,V_ADC

SetVoltage(channel=7, voltage=255)
time.sleep(0.02)
I, V, I_ADC, V_ADC = ReadADC()
print I,V,I_ADC,V_ADC

SetVoltage(channel=5, voltage=255)
time.sleep(0.02)
I, V, I_ADC, V_ADC = ReadADC()
print I,V,I_ADC,V_ADC


CloseFtdi() # Ends communication with RDO board



