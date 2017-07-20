#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "3.0"

##For the 16 channel board, just uncomment the lines with the #**# symbol.

import os
import io
import sys
import time
from time import strftime, sleep
import datetime
import shutil
from definitions import *

ADCaddress = (0x21, 0x23, 0x22, 0x24)
POTaddress = (0x2C, 0x2D, 0x2E, 0x2F) #the first two are for master board, the latter for slave. Each one controls 4 channels.
THaddress = (0x31, 0x33, 0x43, 0x51) #pot addresses
IOaddress = (0x20, 0x26) #addresses of the IO modules that enable channels.

##for bias voltage
DACaddress = (0x32, 0x50)

# Define I2C link address
def I2CLink(isSpecial=False):
    if isSpecial: return 0xB
    else: return 0xA

def GetLatchStatus():
    LUstate_0 = ReadFromDevice(I2CLink(), IOaddress[0], 1)
    LUstate_0 = [x for x in LUstate_0]
    #**#LUstate_1 = ReadFromDevice(I2CLink(), IOaddress[1], 1)
    #**#LUstate_1 = [bin(x) for x in LUstate_1]
    return LUstate_0 ##,LUstate_1

def UnlatchAll():
    print 'Unlatching ALL channels'
    WriteToDevice(I2CLink(), IOaddress[0], 0x00) 
    WriteToDevice(I2CLink(), IOaddress[0], 0xFF)  #NEEDED to end the high-Z state of IO.
    #**#WriteToDevice(I2CLink(), IOaddress[1], int(0xFF)) 
    #**#WriteToDevice(I2CLink(), IOaddress[1], 0xFF) 
    time.sleep(0.02)
    return 
    
def Unlatch(channel):
    print 'Unlatching channel #%d' %(channel)
    if channel<8:
        IO = IOaddress[0]
    else: 
        IO = IOaddress[1]
    WriteToDevice(I2CLink(), IO, int(0xFF^2**channel)) 
    WriteToDevice(I2CLink(), IO, 0xFF)  #NEEDED to end the high-Z state of IO.
    time.sleep(0.02)
    return 


def RaiseThresholdsToMax():
    #This function raises the threshold of all channels to the maximum.
    print 'Raising thresholds of all channels to maximum...' 
    I2CData = [0x3F, 0xFF, 0xFF]
    WriteToDevice(I2CLink(), THaddress[0], *I2CData)    
    WriteToDevice(I2CLink(), THaddress[1], *I2CData)
    #**#WriteToDevice(I2CLink(), THaddress[2], *I2CData)   
    #**#WriteToDevice(I2CLink(), THaddress[3], *I2CData)
    return

def LowerThresholdsToMin():
    #This function raises the threshold of all channels to the maximum.
    print 'Lowering thresholds of all channels to minimum..' 
    I2CData = [ 0x3F, 0x00, 0x00]
    WriteToDevice(I2CLink(), THaddress[0], *I2CData)  #all thresholds  
    WriteToDevice(I2CLink(), THaddress[1], *I2CData)
    #**#WriteToDevice(I2CLink(), THaddress[2], *I2CData)  #all thresholds  
    #**#WriteToDevice(I2CLink(), THaddress[3], *I2CData)

def AddressConfigRegADC():
    #Need to send this command before reading ADC values. 
    print 'Addressing Conf Register' 
    I2CData         = [0x2, 0xF, 0xF8] ###change for the new boards 
    WriteToDevice(I2CLink(), ADCaddress[0], *I2CData) 
    WriteToDevice(I2CLink(), ADCaddress[1], *I2CData) 
    #**#WriteToDevice(I2CLink(), ADCaddress[2], *I2CData) 
    #**#WriteToDevice(I2CLink(), ADCaddress[3], *I2CData) 
    return

def GetADC(value):
    return int((value>>2) % 1024)

class prettyfloat(float):
    def __repr__(self):
        return "%0.2f" % self

def ReadADC():
    print ' Reading ALL ADCs' 
    adcdeviceA = ADCaddress[0]
    adcdeviceB = ADCaddress[1]
    #**#adcdeviceC = ADCaddress[2]
    #**#adcdeviceD = ADCaddress[3]
   
    NumBytesToRead = 16
    I2CData        = [0x70]##change this for new board
    DataA = ReadRSFromDevice(I2CLink(), adcdeviceA, NumBytesToRead, *I2CData) #reading the data of first ADC
    DataB = ReadRSFromDevice(I2CLink(), adcdeviceB, NumBytesToRead, *I2CData) #reading the data of second ADC  
    #**#DataC = ReadRSFromDevice(I2CLink(), adcdeviceC, NumBytesToRead, *I2CData) #reading the data of first ADC
    #**#DataD = ReadRSFromDevice(I2CLink(), adcdeviceD, NumBytesToRead, *I2CData) #reading the data of second ADC  

    VADC_A = [GetADC(DataA[6-2*x+1]) for x in range(0,4)] #this funny scheme is because of the way the data is returned in ReadRSFromDevice
    IADC_A = [GetADC(DataA[6-2*x]) for x in range(0,4)]
    VADC_B = [GetADC(DataB[6-2*x+1]) for x in range(0,4)]
    IADC_B = [GetADC(DataB[6-2*x]) for x in range(0,4)]

    #**#VADC_C = [GetADC(DataC[6-2*x+1]) for x in range(0,4)] #this funny scheme is because of the way the data is returned in ReadRSFromDevice
    #**#IADC_C = [GetADC(DataC[6-2*x]) for x in range(0,4)]
    #**#VADC_D = [GetADC(DataD[6-2*x+1]) for x in range(0,4)]
    #**#IADC_D = [GetADC(DataD[6-2*x]) for x in range(0,4)]

    V_ADC = VADC_A + VADC_B ## + VADC_C + VADC_D
    I_ADC = IADC_A + IADC_B ## + IADC_C + IADC_D
    V = [ (2.999/1024.0)*x for x in V_ADC]
    I = [ x/1024.0*2.992/10.0/0.05 for x in I_ADC] # this assumes a resistance of 50 mOhm.
    V = map(prettyfloat, V)
    I = map(prettyfloat, I)
    return I, V, I_ADC, V_ADC


def SetVoltage(channel, voltage):
    print "Setting voltage of channel %d to %d [DAC]" %(channel, voltage) 
    if channel < 4: pot = POTaddress[0]
    elif channel< 8: pot = POTaddress[1]
    else: return 
    #**#elif channel<12: pot = POTaddress[2]
    #**#elif channel<16  pot = POTaddress[3]
    WriteToDevice(I2CLink(), pot, (channel %4), voltage) 
    time.sleep(0.02)
    return

def EnableBias(channel):
    WriteToDevice(0x20, 0x80) 
    return

def ShutDownBias():
    WriteToDevice(0x26, 0xFF)
    return

def SetBiasVoltage(channel, voltage):
    print "Setting Bias Voltage of channel %d to %d [DAC]" %(channel, voltage) 
    if channel < 4: address = DACaddress[0]
    else: address = DACaddress[1]
    WriteToDevice(I2CLink(), address, 0x3F, VAL, 0x00)
    time.sleep(0.02)
    return

def SetThreshold(channel, value):     #Setting threshold of a single channel.    #channel in [0,7].    #threshold value 0--255. 
    if channel < 4: thaddress = THaddress[0]
    elif channel < 8 : thaddress = THaddress[1]
    #**#elif channel < 12 : thaddress = THaddress[2]
    #**#elif channel < 16 : thaddress = THaddress[3]
    else: return

    WriteToDevice(I2CLink(), thaddress, (3<<4 |channel%4), int(value), int(value)) #see
    return
