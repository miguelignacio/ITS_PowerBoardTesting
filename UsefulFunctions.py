#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "2.0"
__status__ = "Prototype"

import os
import io
import sys
import time
from time import strftime, sleep
import datetime
import shutil
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from definitions import ReadRSFromDeviceToArray
ADCaddress = (0x21, 0x23, 0x22, 0x24)
POTaddress = (0x2C, 0x2D, 0x2E, 0x2F) #the first two are for master board, the latter for slave. Each one controls 4 channels.
THaddress = (0x31, 0x33, 0x43, 0x51)
IOaddress = (0x20, 0x26) #addresses of the IO modules that enable channels. First if for master board, second for slave board.
boardtype = ("Master", "Slave")


def RaiseThresholdsToMax():
    #This function raises the threshold of all channels to the maximum.
    print 'Raising thresholds of all channels to maximum' 
    for i in range(0, len(THaddress), 1):
        WriteToDevice(int(THaddress[i]), 0x3F, 0xFF, 0xFF)  #all thresholds  

def LowerThresholdsToMin():
    #This function raises the threshold of all channels to the maximum.
    print 'Lowering thresholds of all channels to maximum'
    for i in range(0, len(THaddress), 1):
        WriteToDevice(THaddress[i], 0x3F, 0x00, 0x00) # Set all thresholds low to latch
   
def AddressConfigRegADC(master = True):
    #Need to send this command before reading ADC values. There are two ADCs per board.
    if master:
        WriteToDevice(ADCaddress[0], 0x02, 0x0f, 0xf8) 
        WriteToDevice(ADCaddress[1], 0x02, 0x0f, 0xf8) 
    else:
        WriteToDevice(ADCaddress[2], 0x02, 0x0f, 0xf8) 
        WriteToDevice(ADCaddress[3], 0x02, 0x0f, 0xf8) 
    return


def GetCurrentinAmps(value):
    Imon = ((value>>2) % 1024 )/1024.0*2.992/10.0/0.05 # this assumes a resistance of 50 mOhm.
    return Imon

def GetADC(value):
    return (value>>2) % 1024

def GetVoltageInVolts(value):
    Vmon = (2.999/1024)*((value>>2) % 1024)
    return Vmon


def ReadADC(master = True):
    if master:
        adcdeviceA = ADCaddress[0]
        adcdeviceB = ADCaddress[1]
    else:
        adcdeviceA = ADCaddress[2]
        adcdeviceB = ADCaddress[3]

    DataA = ReadRSFromDeviceToArray(adcdeviceA, 16, 0x70) #reading the data of first ADC
    DataB = ReadRSFromDeviceToArray(adcdeviceB, 16, 0x70) #reading the data of second ADC
    del DataA[-1]
    del DataB[-1]
    Data = DataA+DataB
    V = [GetVoltageInVolts(Data[2*x]) for x in range(0,8)] #the even values are voltage measurement 
    I = [GetCurrentinAmps(Data[2*x+1]) for x in range(0,8)] #the odd values are current measurements
    #print 'Currents = ' , I
    V_ADC = [GetADC(Data[2*x]) for x in range(0,8)]
    I_ADC = [GetADC(Data[2*x+1]) for x in range(0,8)] 
   
    return I, V, I_ADC, V_ADC


def SetVoltage(master, channel, voltage):
    print "Setting voltage of channel %d to %d [DAC]" %(channel, voltage) 
    #Finding the address of the POT that controls the voltage for ths particular channel.
    if master:
        if channel < 4: pot = POTaddress[0]
        else: pot = POTaddress[1]
    else:
        if channel < 4: pot = POTaddress[2]
        else: pot = POTaddress[3]
    #Command that 
    WriteToDevice(pot, (channel %4), voltage) 
    return

def PrintLatchStatus(master = True):
    if master:
        LUdevice = IOaddress[0]
    else:
        LUdevice = IOaddress[1]
    LUstate = ReadFromDevice(LUdevice, 1)
    print "Latch status: " , bin(LUstate)
    return LUstate

def Unlatch(master, channel):
    #Unlatches, i.e enables, a given channel
    print "Unlatching channel %i" %channel
    if master:
        IO = IOaddress[0]
    else: 
        IO = IOaddress[1]
    WriteToDevice( IO , 0xFF^ 2**channel) #ENABLE ONE CHANNEL
    WriteToDevice( IO , 0xFF) #NEEDED to end the high-Z state of IO.
    time.sleep(0.1) #rest a little bit
    PrintLatchStatus(master)
    return

def SetThreshold(master, channel, value):     #Setting threshold of a single channel.    #channel in [0,7].    #threshold value 0--255. 
    if master:
        thaddress = THaddress[int(channel/4)]
    else:
        thaddress = THaddress[2+int(channel/4)]
    WriteToDevice(thaddress, (3<<4 |channel%4), int(value), int(value)) #see LTasdasd datasheet page X. 
    return
