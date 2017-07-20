#!/usr/bin/env python
import os
import io
import sys
import time
import array
import matplotlib.pyplot as plt
from definitions import WriteToDevice
from definitions import ReadFromDevice 
from definitions import ReadRSFromDevice 
from definitions import AppendWriteToDevice
from definitions import AppendReadFromDevice
from definitions import AppendReadRSFromDevice
from definitions import SendPacket
from definitions import DecodeI2CData

  
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
        return "%0.2f" % self

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

def RaiseThresholdsToMax(PowerUnitID = 1):
    print 'Raising thresholds of all channels to maximum...' 

    LinkType = ThresPowerLink
    I2CData = [0x3F, 0xFF, 0xFF]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[0], *I2CData)    
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[1], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[2], *I2CData)   
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[3], *I2CData)

def LowerThresholdsToMin(PowerUnitID = 1):
    print 'Lowering thresholds of all channels to minimum...' 

    LinkType = ThresPowerLink
    I2CData = [ 0x3F, 0x00, 0x00]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[0], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[1], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[2], *I2CData)
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[3], *I2CData)

def SetThreshold(PowerUnitID, channel, value): 
    print 'Setting thresholds for channel #%d' % (channel)
    if (channel > 16):
        print 'Channel #%d does not exist' % (channel)
    if (value >= (1<<12)):
        print 'DAC value is higher than allowed: %h' % (value)

    LinkType = ThresPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[channel/4], (3<<4 | channel%4), value/16, ((value%16<<4)))

def SetThresholdAll(PowerUnitID, value): 
    print 'Setting all thresolds' % (channel)
    if (value >= (1<<12)):
        print 'DAC value is higher than allowed: %h' % (value)

    LinkType = ThresPowerLink
    for channel in range (0, 16):
        WriteToDevice(I2CLink(PowerUnitID, LinkType), ThresPowerAddress[channel/4], (3<<4 | channel%4), value/16, ((value%16<<4)))

def ConfigurePowerADC(PowerUnitID = 1):
    print "Configuring Power ADCs..."

    LinkType = ADCLink
    for SlaveAddress in ADCAddress:
        I2CData = [0xB, 0x2] # Setting the advanced configuration register
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    
        I2CData = [0x0, 0x1] # Setting the configuration register
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    

def ConfigureBiasADC(PowerUnitID = 1):
    print "Configuring Bias ADCs..."

    LinkType = ADCBiasLink
    SlaveAddress = ADCBiasAddress
    I2CData = [0xB, 0x2] # Setting the advanced configuration register
    WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    
    I2CData = [0x0, 0x1] # Setting the configuration register
    WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)    

def ReadPowerADC(PowerUnitID = 1):
    print "Reading the ADC channels for power..."

    LinkType = ADCLink
    NumOfBytesToRead = 2
    ADCData = []
    for SlaveAddress in ADCAddress:
        for channel in range(0, 8):
            I2CData = [0x20 + channel]
            WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
            ADCValue = ReadFromDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)
            if channel%2:
                ADCData.append( (((ADCValue[0]>>4)/4096.)*2.56 - 0.25)/(0.005*150) )
            else:
                ADCData.append( ((ADCValue[0]>>4)/4096.)*2.56 )

    return ADCData

def ReadBiasADC(PowerUnitID = 1):
    print "Reading the ADC channels for bias..."

    LinkType = ADCBiasLink
    NumOfBytesToRead = 2
    ADCData = []
    SlaveAddress = ADCBiasAddress
    for channel in range(0, 8):
        I2CData = [0x20 + channel]
        WriteToDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
        ADCValue = ReadFromDevice(I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)
        ADCData.append( ((ADCValue[0]>>4)/4096.)*2.56 )

    return ADCData

def SetPowerVoltageAll(PowerUnitID, voltage):
    for channel in range (0, 16):
        SetPowerVoltage(PowerUnitID, channel, voltage)

def SetPowerVoltage(PowerUnitID, channel, voltage):
    print 'Setting power voltage of channel %d to %d [DAC]' %(channel, voltage) 
    if (channel > 16):
        print 'Channel #%d for power does not exist' %(channel)

    LinkType = PotPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), PotPowerAddress[channel/4], channel%4, int(voltage))

def SetBiasVoltage(PowerUnitID, voltage):
    print 'Setting bias voltage to %d [DAC]' %(voltage) 

    LinkType = PotBiasLink
    I2CData = [0x11, int(voltage)]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), PotBiasAddress, *I2CData) 

def PrintPowerLatchStatus(PowerUnitID = 1):
    print 'Reading status of power channels...'
    LinkType = IOExpanderPowerLink
    LUstate = (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 1))[0]
    LUstate = LUstate | (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 1))[0]<<8
    return LUstate

def PrintBiasLatchStatus(PowerUnitID = 1):
    print 'Reading status of bias channels...'
    LinkType = IOExpanderBiasLink
    LUstate = (ReadFromDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 1))[0]
    return LUstate

def UnlatchPowerAll(PowerUnitID = 1):
    print 'Unlatching ALL power channels'
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 0xFF) 
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 0xFF) 
    
def UnlatchBiasAll(PowerUnitID = 1):
    print 'Unlatching ALL bias channels'
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 0x00) 

def UnlatchPower(PowerUnitID, channel):
    print 'Unlatching power channel #%d' %(channel)
    if (channel > 16):
        print "Channel %d for power does not exist" % (channel)
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[channel/8], int(0x00^2**(channel%8))) 

def UnlatchPowerWithMask(PowerUnitID, mask):
    print 'Unlatching power channel mask %d' %(mask)

    LinkType = IOExpanderPowerLink
    if (mask & 0xFF):
        WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], mask & 0xFF) 
    if ((mask>>8) & 0xFF):
        WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], (mask>>8) & 0xFF) 

def UnlatchBias(channel):
    print 'Unlatching bias channel #%d' %(channel)
    if (channel > 8):
        print 'Channel #%d for bias does not exist' % (channel)
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, int(0xFF^2**channel)) 

def DisablePowerAll(PowerUnitID = 1):
    print 'Disabling ALL power channels'
    LinkType = IOExpanderPowerLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[0], 0x00) 
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderPowerAddress[1], 0x00) 

def DisableBiasAll(PowerUnitID = 1):
    print 'Disabling ALL bias channels'
    LinkType = IOExpanderBiasLink
    WriteToDevice(I2CLink(PowerUnitID, LinkType), IOExpanderBiasAddress, 0xFF) 

def ConfigureRTD(PowerUnitID = 1):
    print "Configuring RTD..."

    LinkType = BridgeTempLink
    I2CData = [0x1, 0x80, 0xC2]
    WriteToDevice(I2CLink(PowerUnitID, LinkType), BridgeTempAddress, *I2CData) 

def ReadRTD(PowerUnitID = 1):
    print "Reading from RTD..."  
  
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

# Can read and write to digital potentiometers for power
def AddressPowerDigitalPotentiometers(PowerUnitID = 1):
    voltageSetting = 0x97
    for channel in range (0, 16):
        SetPowerVoltage(PowerUnitID, channel, voltageSetting) 
        VoltageReadout = GetPowerVoltage(PowerUnitID, channel)
        if (voltageSetting != voltageReadout):
            print "Voltage readout for power digital potentiometers failed for channel %s." % (channel)
            exit(EXIT_FAILURE)

# Can only write to digital potentiometers, firmware will check the acknowledges
def AddressBiasDigitalPotentiometers(PowerUnitID = 1):
    voltageSetting = 0x97
    for channel in range (0, 16):
        SetBiasVoltage(PowerUnitID, voltageSetting) 

# Can read and write to IO expanders for power
def AddressPowerIOExpander(PowerUnitID = 1):
    IOSetting = 0x1
    for channel in range (0, 16):
        RaiseThesholdsToMax(PowerUnit)
        UnlatchPower(PowerUnitID, channel) 
        time.sleep(0.1)
        LatchStatus = (PrintPowerLatchStatus(PowerUnitID) >> channel) & 0x1
        LowerThesholdsToMin(PowerUnit)
        if (IOSetting != LatchStatus):
            print "Mismatch between IO setting and latch status for power channel %s." % (channel)
            exit(EXIT_FAILURE)

# Can read and write to IO expanders for bias
def AddressBiasIOExpander(PowerUnitID = 1):
    IOSetting = 0x1
    for channel in range (0, 8):
        UnlatchBias(PowerUnitID, channel) 
        LatchStatus = (PrintBiasLatchStatus(PowerUnitID) >> channel) & 0x1
        DisableBiasAll(PowerUnitID)
        if (IOSetting != LatchStatus):
            print "Mismatch between IO setting and latch status for bias channel %s." % (channel)

# Can only write to DACs, firmware will check the acknowledges
def AddressDAC(PowerUnitID = 1):
    threshold = 0xAAA
    for channel in range (0, 16):
        SetThreshold(PowerUnitID, channel, threshold) 

# Will only write to ADC for power, reads will be deeply checked with other functions
def AddressPowerDAC(PowerUnitID = 1):
    ConfigurePowerADC(PowerUnitID)

# Will only write to ADC for bias, reads will be deeply checked with other functions
def AddressPowerDAC(PowerUnitID = 1):
    ConfigureBiasADC(PowerUnitID)

# Will only write to ADC for bias, reads will be deeply checked with other functions
def AddressRTD(PowerUnitID = 1):
    ConfigureRTD(PowerUnitID)

def GetStabilityTestData(Datafile):
    VoltageData = [[] for x in xrange(34)]
    CurrentData = [[] for x in xrange(34)]
    TempData = [[] for x in xrange(2)] 

    noRTD = 0 # Select if to exclude the RTD

    if (noRTD == 0):
        numberOfBytesPerCycle = 320
    else:
        numberOfBytesPerCycle = 328

    with open(Datafile,'rb') as f:
        while True:
            buf = f.read(numberOfBytesPerCycle) # 4 byte per meas * (40 (V and I) channels + 1 RTD) * 2 PU
            if len(buf) != numberOfBytesPerCycle: break
            for i in range (0, 32):
                VoltageData[i].append(GetPowerVoltageData(buf, i))
                CurrentData[i].append(GetPowerCurrentData(buf, i))
            for k in range (0, 2):
                VoltageData[32 + k].append(GetBiasVoltageData(buf, k))
                CurrentData[32 + k].append(GetBiasCurrentData(buf, k))
            if (noRTD == 0):
                for j in range (0, 2):
                    TempData[j].append(GetTempData(buf, j))

    return VoltageData, CurrentData, TempData

def GetVoltageScanPowerTestData(Datafile):
    numberOfPowerChannelsPerPU = 16
    numberOfBytesPerSample   = numberOfPowerChannelsPerPU * 2 * 4 # Bytes acquires per sample on all channels (2 is because V and I, 4 is bytes per read)
    numberOfSamplesPerPoint  = 10  # Number of ADC samples per voltage setting

    PowerVoltageData      = [[] for x in xrange(numberOfPowerChannelsPerPU)]
    PowerVoltageNoiseData = [[] for x in xrange(numberOfPowerChannelsPerPU)]
    PowerCurrentData      = [[] for x in xrange(numberOfPowerChannelsPerPU)]
    PowerCurrentNoiseData = [[] for x in xrange(numberOfPowerChannelsPerPU)]

    endOfFile = 0;

    with open(Datafile,'rb') as f:
        while True:
            VoltageSamples = [[] for x in xrange(numberOfPowerChannelsPerPU)]
            CurrentSamples = [[] for x in xrange(numberOfPowerChannelsPerPU)] 
            for j in range (0, numberOfSamplesPerPoint):
                 buf = f.read(numberOfBytesPerSample) 
                 if len(buf) != numberOfBytesPerSample:
                     endOfFile = 1
                     break
                 for i in range (0, numberOfPowerChannelsPerPU):
                     VoltageSamples[i].append(GetPowerVoltageData(buf, i))
                     CurrentSamples[i].append(GetPowerCurrentData(buf, i))
       
            if (endOfFile == 1):
                break
            
            for k in range (0, numberOfPowerChannelsPerPU):
                VoltageAverage = 0.
                CurrentAverage = 0.
                for s in range (0, numberOfSamplesPerPoint):
                    VoltageAverage = VoltageAverage + (VoltageSamples[k][s]/numberOfSamplesPerPoint)
                    CurrentAverage = CurrentAverage + (CurrentSamples[k][s]/numberOfSamplesPerPoint)
                PowerVoltageData[k].append(VoltageAverage)
                PowerCurrentData[k].append(CurrentAverage)
                print VoltageAverage, CurrentAverage

                VoltageNoise = 0.000001
                CurrentNoise = 0.000001
                for t in range (0, numberOfSamplesPerPoint):
                    VoltageNoise = VoltageNoise + (VoltageSamples[k][t] - VoltageAverage)**2
                    CurrentNoise = CurrentNoise + (CurrentSamples[k][t] - CurrentAverage)**2
                    
                PowerVoltageNoiseData[k].append((CurrentNoise**(1/2.0))/numberOfSamplesPerPoint)
                PowerCurrentNoiseData[k].append((CurrentNoise**(1/2.0))/numberOfSamplesPerPoint)
   
    return PowerVoltageData, PowerVoltageNoiseData, PowerCurrentData, PowerCurrentNoiseData

def GetVoltageScanBiasTestData(Datafile):
    numberOfBiasChannelsPerPU = 1
    numberOfBytesPerSample   = 8 * 4 # Bytes acquires per sample on all channels (2 is because V and I, 4 is bytes per read)
    numberOfSamplesPerPoint  = 10  # Number of ADC samples per voltage setting

    BiasVoltageData      = [[] for x in xrange(numberOfBiasChannelsPerPU)]
    BiasVoltageNoiseData = [[] for x in xrange(numberOfBiasChannelsPerPU)]
    BiasCurrentData      = [[] for x in xrange(numberOfBiasChannelsPerPU)]
    BiasCurrentNoiseData = [[] for x in xrange(numberOfBiasChannelsPerPU)]

    endOfFile = 0;

    with open(Datafile,'rb') as f:
        while True:
            VoltageSamples = [[] for x in xrange(numberOfBiasChannelsPerPU)]
            CurrentSamples = [[] for x in xrange(numberOfBiasChannelsPerPU)] 
            for j in range (0, numberOfSamplesPerPoint):
                 buf = f.read(numberOfBytesPerSample) 
                 if len(buf) != numberOfBytesPerSample:
                     endOfFile = 1
                     break
                 for i in range (0, numberOfBiasChannelsPerPU):
                     VoltageSamples[i].append(GetBiasVSVoltageData(buf, i))
                     CurrentSamples[i].append(GetBiasVSCurrentData(buf, i))
       
            if (endOfFile == 1):
                break
            
            for k in range (0, numberOfBiasChannelsPerPU):
                VoltageAverage = 0.
                CurrentAverage = 0.
                for s in range (0, numberOfSamplesPerPoint):
                    VoltageAverage = VoltageAverage + (VoltageSamples[k][s]/numberOfSamplesPerPoint)
                    CurrentAverage = CurrentAverage + (CurrentSamples[k][s]/numberOfSamplesPerPoint)
                BiasVoltageData[k].append(VoltageAverage)
                BiasCurrentData[k].append(CurrentAverage)
                print VoltageAverage, CurrentAverage

                VoltageNoise = 0.000001
                CurrentNoise = 0.000001
                for t in range (0, numberOfSamplesPerPoint):
                    VoltageNoise = VoltageNoise + (VoltageSamples[k][t] - VoltageAverage)**2
                    CurrentNoise = CurrentNoise + (CurrentSamples[k][t] - CurrentAverage)**2
                    
                BiasVoltageNoiseData[k].append((CurrentNoise**(1/2.0))/numberOfSamplesPerPoint)
                BiasCurrentNoiseData[k].append((CurrentNoise**(1/2.0))/numberOfSamplesPerPoint)
   
    return BiasVoltageData, BiasVoltageNoiseData, BiasCurrentData, BiasCurrentNoiseData

def GetPowerVoltageData(DataBuffer, index):
    VoltageDig = int(DataBuffer[8*index + 1].encode('hex'), 16) << 8 | int(DataBuffer[8*index].encode('hex'), 16)
    return (VoltageDig/4096.)*2.56

def GetPowerCurrentData(DataBuffer, index):
    CurrentDig = int(DataBuffer[8*index + 5].encode('hex'), 16) << 8 | int(DataBuffer[8*index + 4].encode('hex'), 16)
    return ((CurrentDig/4096.)*2.56 - 0.25)/(0.005*150)

def GetBiasVoltageData(DataBuffer, index):
    VoltageDig = int(DataBuffer[256 + 32*index + 9].encode('hex'), 16) << 8 | int(DataBuffer[256 + 32*index + 8].encode('hex'), 16)
    return (VoltageDig/4096.)*2.56*-2.

def GetBiasCurrentData(DataBuffer, index):
    CurrentDig = int(DataBuffer[256 + 32*index + 1].encode('hex'), 16) << 8 | int(DataBuffer[256 + 32*index].encode('hex'), 16)
    return (CurrentDig/4096.)*2.56

def GetBiasVSVoltageData(DataBuffer, index):
    VoltageDig = int(DataBuffer[32*index + 9].encode('hex'), 16) << 8 | int(DataBuffer[32*index + 8].encode('hex'), 16)
    return (VoltageDig/4096.)*2.56*-2.

def GetBiasVSCurrentData(DataBuffer, index):
    CurrentDig = int(DataBuffer[32*index + 1].encode('hex'), 16) << 8 | int(DataBuffer[32*index].encode('hex'), 16)
    return (CurrentDig/4096.)*2.56

def GetTempData(DataBuffer, index):
    TempDig = int(DataBuffer[320 + 4*index + 1].encode('hex'), 16) << 8 | int(DataBuffer[320 + 4*index].encode('hex'), 16)
    return (TempDig - 8192.)/31.54

def PlotPowerAnalogVoltages(PowerUnitID, VoltageData):
    if (PowerUnitID == 1):
        VoltageChannels = 0x5555
    else:
        VoltageChannels = 0x55550000
    PlotStabilityTestData(VoltageData, VoltageChannels, [[] for i in range (0, 34)], 0x0000, [[] for i in range (0, 3)], 0x0)

def PlotPowerDigitalVoltages(PowerUnitID, VoltageData):
    if (PowerUnitID == 1):
        VoltageChannels = 0xAAAA
    else:
        VoltageChannels = 0xAAAA0000
    PlotStabilityTestData(VoltageData, VoltageChannels, [[] for i in range (0, 34)], 0x0000, [[] for i in range (0, 3)], 0x0)

def PlotBiasVoltages(PowerUnitID, VoltageData):
    if (PowerUnitID == 1):
        VoltageChannels = 0x100000000
    elif (PowerUnitID == 2):
        VoltageChannels = 0x200000000
    else:
        VoltageChannels = 0x300000000

    PlotStabilityTestData(VoltageData, VoltageChannels, [[] for i in range (0, 34)], 0x0000, [[] for i in range (0, 3)], 0x0)

def PlotBiasVSVoltages(PowerUnitID, VoltageData):
    PlotStabilityTestData(VoltageData, 0x1, [[] for i in range (0, 34)], 0x0000, [[] for i in range (0, 3)], 0x0)

def PlotBiasVSCurrents(PowerUnitID, CurrentData):
    PlotStabilityTestData([[] for i in range (0, 34)], 0x0000, CurrentData, 0x1, [[] for i in range (0, 3)], 0x0)

def PlotPowerAnalogCurrents(PowerUnitID, CurrentData):
    if (PowerUnitID == 1):
        CurrentChannels = 0x5555
    else:
        CurrentChannels = 0x55550000
    PlotStabilityTestData([[] for i in range (0, 34)], 0x0000, CurrentData, CurrentChannels, [[] for i in range (0, 3)], 0x0)

def PlotPowerDigitalCurrents(PowerUnitID, CurrentData):
    if (PowerUnitID == 1):
        CurrentChannels = 0xAAAA
    else:
        CurrentChannels = 0xAAAA0000
    PlotStabilityTestData([[] for i in range (0, 34)], 0x0000, CurrentData, CurrentChannels, [[] for i in range (0, 3)], 0x0)

def PlotBiasCurrents(PowerUnitID, CurrentData):
    if (PowerUnitID == 1):
        CurrentChannels = 0x100000000
    elif (PowerUnitID == 2):
        CurrentChannels = 0x200000000
    else:
        CurrentChannels = 0x300000000

    PlotStabilityTestData([[] for i in range (0, 34)], 0x0000, CurrentData, CurrentChannels, [[] for i in range (0, 3)], 0x0)

def PlotTemperatures(PowerUnitID, TempData):
    if (PowerUnitID == 1):
        TempChannels = 0x1
    elif (PowerUnitID == 2):
        TempChannels = 0x2
    else:
        TempChannels = 0x3
    
    PlotStabilityTestData([[] for i in range (0, 34)], 0x0000, [[] for i in range (0, 3)], 0x0000, TempData, TempChannels)

def PlotStabilityTestData(VoltageData, VoltageChannels, CurrentData, CurrentChannels, TempData, TempChannels):
    for i in range (0, 34):
        if ((VoltageChannels >> i) & 0x1):
            label = "Ch" + str(i) + " voltage"
            plt.plot(VoltageData[i], label=label)
        if ((CurrentChannels >> i) & 0x1):
            label = "Ch" + str(i) + " current"
            plt.plot(CurrentData[i], label=label)

    if (TempChannels & 0x1):
        label = "PU1" + " temperature"
        plt.plot(TempData[0], label=label)
    if (TempChannels & 0x2):
        label = "PU2" + " temperature"
        plt.plot(TempData[1], label=label)

    plt.legend()
    plt.show() 

def GetPowerADCData(PowerUnitID = 1):
    print "Getting Power ADC data..."

    LinkType = ADCLink
    NumOfBytesToRead = 2
    ListOfCommands = []
    DataBuffer = []
    ADCData = []
    for SlaveAddress in ADCAddress:
        for channel in range(0, 8):
            I2CData = [0x20 + channel]
            AppendWriteToDevice(ListOfCommands, I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
            AppendReadFromDevice(ListOfCommands, DataBuffer, I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)

    SendPacket(ListOfCommands, DataBuffer)
     
    DecodeI2CData(DataBuffer, 0, ADCData, 2, 0xFFF0, 32)

    return ADCData

def GetBiasADCData(PowerUnitID = 1):
    print "Reading the ADC channels..."

    LinkType = ADCBiasLink
    NumOfBytesToRead = 2
    ListOfCommands = []
    DataBuffer = []
    ADCData = []
    SlaveAddress = ADCBiasAddress
    for channel in range(0, 8):
        I2CData = [0x20 + channel]
        AppendWriteToDevice(ListOfCommands, I2CLink(PowerUnitID, LinkType), SlaveAddress, *I2CData)
        AppendReadFromDevice(ListOfCommands, DataBuffer, I2CLink(PowerUnitID, LinkType), SlaveAddress, NumOfBytesToRead)

    SendPacket(ListOfCommands, DataBuffer)

    DecodeI2CData(DataBuffer, 0, ADCData, 2, 0xFFF0, 8)

    return ADCData

def GetRTDData(PowerUnitID = 1):
    print "Getting data from RTD..."  
  
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

    return ResistanceValue
