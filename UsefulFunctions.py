#!/usr/bin/env python
import os
import io
import sys
import time
from time import strftime, sleep
import datetime
import shutil
from definitions import *

# I2C links for the various power board devices
BridgeTempLink      = "main"
ADCLink             = "main"
PotPowerLink        = "main"
ThresPowerLink      = "main"
IOExpanderPowerLink = "aux"
ADCBiasLink         = "main"
PotBiasLink         = "main"
IOExpanderBiasLink  = "main"

# I2C addresses for the various power board devices
BridgeTempAddress      = (0x28)
ADCAddress             = (0x1D, 0x1F, 0x35, 0x37)
ADCBiasAddress         = (0x1E)
PotPowerAddress        = (0x2C, 0x2D, 0x2E, 0x2F)
ThresPowerAddress      = (0x52, 0x60, 0x70, 0x72) 
IOExpanderPowerAddress = (0x38, 0x39) 
PotBiasAddress         = (0x29)
IOExpanderBiasAddress  = (0x38) 

class prettyfloat(float):
    def __repr__(self):
        return "%0.6f" % self

# Define I2C link address
def I2CLink(PowerUnitID, LinkType):
    if   ((PowerUnitID == 1) & (LinkType == "aux")):
        return 0xB
    elif ((PowerUnitID == 1) & (LinkType == "main")):
        return 0xA
    elif ((PowerUnitID == 2) & (LinkType == "aux")):
        return 0xF
    elif ((PowerUnitID == 2) & (LinkType == "main")):
        return 0xE
    else:
        print "Wrong power unit ID or link type provided, exiting..."
        sys.exit(1)

def RaiseThresholdsToMax(PowerUnitID):
    print 'Raising thresholds of all channels to maximum...' 

    LinkType = ThresPowerLink
    I2CData = [0x3F, 0xFF, 0xFF]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[0], *I2CData)    
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[1], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[2], *I2CData)   
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[3], *I2CData)

def LowerThresholdsToMin(PowerUnitID):
    print 'Lowering thresholds of all channels to minimum...' 

    LinkType = ThresPowerLink
    I2CData = [ 0x3F, 0x00, 0x00]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[0], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[1], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[2], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[3], *I2CData)

def SetThreshold(channel, value, PowerUnitID): 
    #print 'Setting thresholds for channel #%d' % (channel)
    if (channel > 16):
        print 'Channel #%d does not exist' % (channel)
    if (value >= (1<<12)):
        print 'DAC value is higher than allowed: %h' % (value)

    LinkType = ThresPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[channel/4], (3<<4 | channel%4), value/16, ((value%16<<4)))

def SetThresholdAll(PowerUnitID, value): 
    #print 'Setting all thresolds'
    if (value >= (1<<12)):
        print 'DAC value is higher than allowed: %h' % (value)

    LinkType = ThresPowerLink
    for channel in range (0, 16):
        WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[channel/4], (3<<4 | channel%4), value/16, ((value%16<<4)))

def ConfigurePowerADC(PowerUnitID):
    print "Configuring Power ADCs..."

    LinkType = ADCLink
    for SlaveAddress in ADCAddress:
        I2CData = [0xB, 0x2] # Setting the advanced configuration register
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    
        I2CData = [0x0, 0x1] # Setting the configuration register
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)   


def ConfigureBiasADC(PowerUnitID):
    print "Configuring Bias ADCs..."

    LinkType = ADCBiasLink
    SlaveAddress = ADCBiasAddress
    I2CData = [0xB, 0x2] # Setting the advanced configuration register
    WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    
    I2CData = [0x0, 0x1] # Setting the configuration register
    WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    

def ReadPowerADC(PowerUnitID):
    #print "Reading the ADC channels for power..."

    LinkType = ADCLink
    NumOfBytesToRead = 2
    V = []
    I = []
    V_ADC = []
    I_ADC = []
    for SlaveAddress in ADCAddress:
        for channel in range(0, 8):
            I2CData = [0x20 + channel]
            WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
            ADCValue = ReadFromDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)
            if channel%2:
                I.append( (((ADCValue[0]>>4)/4096.)*2.56 - 0.25)/(0.005*150) )
                I_ADC.append( (ADCValue[0]>>4)/4096.)
            else:
                V.append( ((ADCValue[0]>>4)/4096.)*2.56 )
                V_ADC.append( (ADCValue[0]>>4)/4096. )
    #print I
    #print V
    return I,V, I_ADC ,V_ADC

def ReadBiasADC(PowerUnitID):
    #print "Reading the ADC channels for bias..."

    LinkType = ADCBiasLink
    NumOfBytesToRead = 2
    Array = []
    SlaveAddress = ADCBiasAddress
    for channel in range(0, 8):
        I2CData = [0x20 + channel]
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
        ADCValue = ReadFromDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)
        Array.append( ((ADCValue[0]>>4)/4096.)*2.56 )
	
  
    I = Array[0]
    V = Array[2]*(-2)
    return I,V


def SetPowerVoltageAll(voltage, PowerUnitID):
    for channel in range (0, 16):
        SetPowerVoltage(channel, voltage, PowerUnitID)
    #time.sleep(0.02)


def SetPowerVoltage(channel, voltage, PowerUnitID=1):
    #print 'Setting power voltage of channel %d to %d [DAC]' %(channel, voltage) 
    if (channel > 16):
        print 'Channel #%d for power does not exist' %(channel)

    LinkType = PotPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), PotPowerAddress[channel/4], channel%4, int(voltage))
    #time.sleep(0.02)

def SetBiasVoltage(voltage, PowerUnitID=1):
    #print 'Setting bias voltage to %d [DAC]' %(voltage) 

    LinkType = PotBiasLink
    I2CData = [0x11, int(voltage)]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), PotBiasAddress, *I2CData) 
    #time.sleep(0.02)

def GetPowerLatchStatus(PowerUnitID):
    #print 'Reading status of power channels...'
    LinkType = IOExpanderPowerLink
    LUstate = (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 1))[0]
    LUstate = LUstate | (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 1))[0]<<8
    return LUstate

def GetBiasLatchStatus(PowerUnitID):
    #print 'Reading status of bias channels...'
    LinkType = IOExpanderBiasLink
    LUstate = (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 1))[0]
    return bin(LUstate)

def UnlatchPowerAll(PowerUnitID):
    #print 'Unlatching ALL power channels'
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 0xFF) 
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 0xFF) 
    #time.sleep(0.02)
    
def UnlatchBiasAll(PowerUnitID):
    #print 'Unlatching ALL bias channels'
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 0x00) 
    #time.sleep(0.02)

def UnlatchPower(channel,PowerUnitID):
    #print 'Unlatching power channel #%d' %(channel)
    if (channel > 16):
        print "Channel %d for power does not exist" % (channel)
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[channel/8], int(0x00^2**(channel%8))) 
    time.sleep(0.02)

def UnlatchBias(channel,PowerUnitID):
    print 'Unlatching bias channel #%d' %(channel)
    if (channel > 8):
        print 'Channel #%d for bias does not exist' % (channel)
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, int(0xFF^2**channel)) 
    #time.sleep(0.02)

def DisablePowerAll(PowerUnitID):
    print 'Disabling ALL power channels'
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 0x00) 
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 0x00) 

def DisableBiasAll(PowerUnitID):
    print 'Disabling ALL bias channels'
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 0xFF) 


def ConfigureRTD(PowerUnitID):
    print "Configuring RTD..."

    LinkType = BridgeTempLink
    I2CData = [0x1, 0x80, 0xC2]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, *I2CData)

def ReadRTD(PowerUnitID):
    #print "Reading from RTD..."

    LinkType = BridgeTempLink
    I2CData = [0x1, 0x1, 0xFF]
    NumOfBytesToRead = 2
    WriteToDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, *I2CData)
    time.sleep(0.1)
    ResistanceValue = ReadFromDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, NumOfBytesToRead)
    I2CData = [0x1, 0x2, 0xFF]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, *I2CData)
    time.sleep(0.1)
    ResistanceValue[0] = ((ResistanceValue[0] & 0xFF) << 7) | ((0xFF & ReadFromDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, NumOfBytesToRead)[0])>>1)
    TemperatureValue = (ResistanceValue[0] - 8192.)/31.54

    return TemperatureValue
