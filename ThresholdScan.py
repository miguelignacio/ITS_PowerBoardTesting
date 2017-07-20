#!/usr/bin/env python
__author__ = "G. Contin, M.Arratia"
__version__ = "2.0"
__status__ = "Prototype"

import os
import io
import sys
import time
from time import strftime, sleep
import datetime
import shutil

from UsefulFunctions import *

import numpy as np
def thresholdScanAll(output, step, start, end, Vset, PowerUnitID):
    print 'Power Unit ID' , PowerUnitID
    OpenFtdi()
    ConfigureRTD(PowerUnitID)
    print 'Entering function threshold scan, '
    LUstate = 0          
    startime = time.strftime("%Y-%m-%d_%H-%M-%S") #Setting timestamp format 
    t1 = datetime.datetime.now() #Getting timestamp
    print t1
    print ' The threshold scan step is %d [DAC]' %(step)
    print "----------threshold scan------------------------"
    LowerThresholdsToMin(PowerUnitID)
    RaiseThresholdsToMax(PowerUnitID)
    print 'Set Power voltage to %d [DAC]' %(Vset) 
    SetPowerVoltageAll(Vset, PowerUnitID)
    sleep(3)

    UnlatchPowerAll(PowerUnitID)
    'Latch status is ' , bin(GetPowerLatchStatus(PowerUnitID)) 
    ConfigurePowerADC(PowerUnitID) #this is necessary to be able to read ADCs
    sleep(0.5)
    print "ch# Th[DAC] Vset [DAC] V [V] I [A]  R [ohm] T[C]"
    print ' Threshold scan loop ' 

    flags = np.ones(16)
    DataBuffer = [] 
    ListOfCommands       = []
    ThresholdData        = []
    DecodedThresholdData = []
    # lower thresholds 
    for j in range (0, 251):

        LinkType     = ThresPowerLink
        threshold = ((256 - j) * 16) - 1
        I2CData = [0x3F, threshold/16, (threshold%16)<<4] 
        ##setting thresholds
        for I2CAddress in ThresPowerAddress: 
            AppendWriteToDevice(ListOfCommands, I2CLink(PowerUnitID, LinkType), I2CAddress, *I2CData)
        AppendSleep(ListOfCommands, 20000) # 20 ms sleep
        ##Readout status
        for I2CAddress in IOExpanderPowerAddress:
            LinkType     = IOExpanderPowerLink
            AppendReadFromDevice(ListOfCommands, DataBuffer, I2CLink(PowerUnitID, LinkType), I2CAddress, 1)    
        ##readout data
        AppendSleep(ListOfCommands, 20000) # 20 ms sleep
        for I2CAddress in ADCAddress:
            for channel in range(0,8):
                I2CData = [0x20 + channel]
                LinkType = ADCLink
                NumOfBytesToRead = 2
                AppendWriteToDevice(ListOfCommands, I2CLink(PowerUnitID, LinkType), I2CAddress, *I2CData)
                
                AppendReadFromDevice(ListOfCommands, DataBuffer, I2CLink(PowerUnitID, LinkType), I2CAddress, NumOfBytesToRead)

        if (j % 25 == 0 and j != 0):
            SendPacket(ListOfCommands, DataBuffer)
            ThresholdData.extend(DataBuffer)
            DataBuffer     = [] 
            ListOfCommands = []


    # Reformatting data
    LUstatus = 0
   
    for i in range (0, len(ThresholdData)):
        if (i%102 == 1 or i%102 == 4):
            if i%2 == 0:
                LUstatus = LUstatus | (ThresholdData[i] << 8)
                DecodedThresholdData.append(LUstatus & 0xFFFF)
                #print bin(LUstatus & 0xFFFF)
            else:
                LUstatus = ThresholdData[i]
        
  
    #print 'len(ThresholdData)' , len(ThresholdData)/102
    print 'len(DecodedThresholData)' , len(DecodedThresholdData)
    #print DecodedThresholdData
    Voltages = [[] for x in xrange(16)]
    Currents = [[] for x in xrange(16)]
    
    j = 0
    for i in range (0, len(ThresholdData)):
        if (((i%102 - 1)%3 == 0) & (i%102 != 1) & (i%102 != 4)):
            if j%2:
                Currents[j/2].append((((ThresholdData[i]>>4 & 0xFFF)/4096.)*2.56 - 0.25)/(0.005*150) *1.00294 +0.013083 )
            else:
                Voltages[j/2].append(((ThresholdData[i]>>4 & 0xFFF)/4096.)*2.56)
         
            j = j + 1
        if (j == 32):
            j = 0
   
    for channel in range(0,16):
        itrigger = -666
        lastLUstate = -999
        for i in range(10, 251):
            #print i, ' ',  Voltages[0][i], ' ' , bin(DecodedThresholdData[i])
            LUstate = DecodedThresholdData[i]
            if ((int(LUstate) & 2**channel) != 2**channel ):
                print 'Channel %i latched in iteration %i' %(channel, i)
                itrigger = i
                lastLUstate = LUstate
                break
       
        didItGoToZero = False
        Vlast = -999
        Ilast = -999
        for i in range(251):
            Vread = Voltages[channel][i]
            Iread = Currents[channel][i]
            if(Vread==0):
                print 'Channel %i voltage went to zero in iteration %i' %(channel, i)
                didItGoToZero = True
                break
            Vlast = Vread
            Ilast = Iread
            
        if(Iread!=0): rload = Vlast/Ilast
                
        if not didItGoToZero:
            Vlast = -999
            Ilast = -999
        T = ReadRTD(PowerUnitID)
        line = "%d %5d %5d %10.2f %8.4f %8.4f %8.4f %s" % (channel, itrigger, Vset, Vlast, Ilast, rload, T, str(bin(LUstate)) )
        with open(output,"ab") as f:
            f.write(str(line) + "\n")
    
    #print len(Voltages[0])
    #print Currents[0]
    #print Voltages[1]

       #if channel%2:
                #    I.append( (((ADCValue[0]>>4)/4096.)*2.56 - 0.25)/(0.005*150) *1.00294 +0.013083 )   
                #    I_ADC.append( (ADCValue[0]>>4)/4096.)
                #else:
                #    V.append( ((ADCValue[0]>>4)/4096.)*2.56 )
                #    V_ADC.append( (ADCValue[0]>>4)/4096. )
                #AppendWriteToDevice(ListOfCommands, I2CLink(PowerUnitID, LinkType), I2CAddress, 


    #print 'DECODED DATA' , DecodedThresholdData 
    #print DataBuffer
    #for thvalue in range(start,end, -1*step): 
    #    threshold = (thvalue * 16) - 1 
    #    I, V, I_ADC, V_ADC = ReadPowerADC(PowerUnitID) 
    #    SetThresholdAll(PowerUnitID, threshold)
    #    sleep(0.02)
    #    LUstate = GetPowerLatchStatus(PowerUnitID)
    #    T = ReadRTD(PowerUnitID)
    #    for channel in range(16): 
    #        if flags[channel]<1: continue
    #        Iread = Vread = 0                   
    #        Vread = V[channel]
    #        Iread = I[channel]
    #	    rload = -1
    #	    if(Iread>0): rload = Vread/Iread
    #        Vread_ADC = V_ADC[channel]
    #        Iread_ADC = I_ADC[channel]
    #        line = "%d %5d %5d %10.2f %8.4f %8.4f %8.4f %s" % (channel, threshold, Vset, Vread, Iread, rload, T, str(bin(LUstate)) )
    #        if ((int(LUstate) & 2**channel) != 2**channel ):
    #            print "!!!!!!!!!!!!!!Channel %d latched at threshold = %5d[DAC], %5d!!!!!!!!!!" %(channel,threshold,thvalue)
    #		print line
    #	        flags[channel] = 0
    #            with open(output,"ab") as f:
    #                f.write(str(line) + "\n")
    #        if (LUstate == 0xff):
    #            break #break the threshold loop
    
    LowerThresholdsToMin(PowerUnitID)
    RaiseThresholdsToMax(PowerUnitID)                
    DisablePowerAll(PowerUnitID)
    CloseFtdi()
    print 'End of the threshold scan function,'
    return 



   
