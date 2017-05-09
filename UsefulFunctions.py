#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "3.0"
import os
import io
import sys
import time
from time import strftime, sleep
import datetime
import shutil
from definitions import WriteToDevice #the new one is almost the same, except one argument. 
from definitions import ReadFromDevice # returns lists now. 
from definitions import ReadRSFromDevice #returns lists now.
 
ADCaddress = (0x21, 0x23, 0x22, 0x24)
POTaddress = (0x2C, 0x2D, 0x2E, 0x2F) #the first two are for master board, the latter for slave. Each one controls 4 channels.
THaddress = (0x31, 0x33, 0x43, 0x51) #pot addresses
IOaddress = (0x20, 0x26) #addresses of the IO modules that enable channels. First if for master board, second for slave board.
boardtype = ("Master", "Slave")

class prettyfloat(float):
    def __repr__(self):
        return "%0.2f" % self

# Define I2C link address
def I2CLink():
    return 0xA

def RaiseThresholdsToMax(master = True):
    #This function raises the threshold of all channels to the maximum.
    print 'Raising thresholds of all channels to maximum...' 
    I2CData = [0x3F, 0xFF, 0xFF]
    if master:
        WriteToDevice(I2CLink(), THaddress[0], *I2CData)    
        WriteToDevice(I2CLink(), THaddress[1], *I2CData)
    else:
	WriteToDevice(I2CLink(), THaddress[2], *I2CData)   
        WriteToDevice(I2CLink(), THaddress[3], *I2CData)

def LowerThresholdsToMin(master = True):
    #This function raises the threshold of all channels to the maximum.
    print 'Lowering thresholds of all channels to minimum..' 
    I2CData = [ 0x3F, 0x00, 0x00]
    if master:
        WriteToDevice(I2CLink(), THaddress[0], *I2CData)  #all thresholds  
        WriteToDevice(I2CLink(), THaddress[1], *I2CData)
    else:
        WriteToDevice(I2CLink(), THaddress[2], *I2CData)  #all thresholds  
        WriteToDevice(I2CLink(), THaddress[3], *I2CData)

def AddressConfigRegADC(master = True):
    #Need to send this command before reading ADC values. There are two ADCs per board.
    print 'Addressing Conf Register' 
    I2CData         = [0x2, 0xF, 0xF8]
    if master:
        WriteToDevice(I2CLink(), ADCaddress[0], *I2CData) 
        WriteToDevice(I2CLink(), ADCaddress[1], *I2CData) 
    else:
        WriteToDevice(I2CLink(), ADCaddress[2], *I2CData) 
        WriteToDevice(I2CLink(), ADCaddress[3], *I2CData) 
    return


def GetADC(value):
    return int((value>>2) % 1024)

def ReadADC(master = True):
    if master:
        adcdeviceA = ADCaddress[0]
        adcdeviceB = ADCaddress[1]
    else:
        adcdeviceA = ADCaddress[2]
        adcdeviceB = ADCaddress[3]
   
    NumBytesToRead = 16
    I2CData        = [0x70]
    DataA = ReadRSFromDevice(I2CLink(), adcdeviceA, NumBytesToRead, *I2CData) #reading the data of first ADC
    DataB = ReadRSFromDevice(I2CLink(), adcdeviceB, NumBytesToRead, *I2CData) #reading the data of second ADC  
    VADC_A = [GetADC(DataA[6-2*x+1]) for x in range(0,4)] #this funny scheme is because of the way the data is returned in ReadRSFromDevice
    IADC_A = [GetADC(DataA[6-2*x]) for x in range(0,4)]
    VADC_B = [GetADC(DataB[6-2*x+1]) for x in range(0,4)]
    IADC_B = [GetADC(DataB[6-2*x]) for x in range(0,4)]
    V_ADC = VADC_A + VADC_B
    I_ADC = IADC_A + IADC_B
    V = [ (2.999/1024.0)*x for x in V_ADC]
    I = [ x/1024.0*2.992/10.0/0.05 for x in I_ADC] # this assumes a resistance of 50 mOhm.
    V = map(prettyfloat, V)
    I = map(prettyfloat, I)
    return I, V, I_ADC, V_ADC


def SetVoltage(channel, voltage, master=True):
    print "Setting voltage of channel %d to %d [DAC]" %(channel, voltage) 
    #Finding the address of the POT that controls the voltage for ths particular channel.
    if master:
        if channel < 4: pot = POTaddress[0]
        else: pot = POTaddress[1]
    else:
        if channel < 4: pot = POTaddress[2]
        else: pot = POTaddress[3]
    WriteToDevice(I2CLink(), pot, (channel %4), voltage) 
    return

def PrintLatchStatus(master = True):
    LUstate = ReadFromDevice(I2CLink(), IOaddress[0], 1)
    return [bin(x) for x in LUstate]

def UnlatchAll(master=True):
    if master:
        IO = IOaddress[0]
    else: 
        IO = IOaddress[1]
    print 'Unlatching ALL channels'
    WriteToDevice(I2CLink(), IO, int(0xFF)) 
    WriteToDevice(I2CLink(), IO, 0xFF)  #NEEDED to end the high-Z state of IO.
    return 
    
def Unlatch(channel,master=True):
    if master:
        IO = IOaddress[0]
    else: 
        IO = IOaddress[1]
    print 'Unlatching channel #%d' %(channel)
    WriteToDevice(I2CLink(), IO, int(0xFF^2**channel)) 
    WriteToDevice(I2CLink(), IO, 0xFF)  #NEEDED to end the high-Z state of IO.
    return 

def SetThreshold(master, channel, value):     #Setting threshold of a single channel.    #channel in [0,7].    #threshold value 0--255. 
    if master:
        thaddress = THaddress[int(channel/4)]
    else:
        thaddress = THaddress[2+int(channel/4)]
    WriteToDevice(I2CLink, thaddress, (3<<4 |channel%4), int(value), int(value)) #see LTasdasd datasheet page X. 
    return
