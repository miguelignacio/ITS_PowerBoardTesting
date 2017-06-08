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

def thresholdScanAll(output, channel, step, start, end, Vset, PowerUnitID):
    print 'Power Unit ID' , PowerUnitID
    OpenFtdi()
    ConfigureRTD(PowerUnitID)
    print 'Entering function threshold scan, '
    LUstate = 0          
    startime = time.strftime("%Y-%m-%d_%H-%M-%S") #Setting timestamp format 
    t1 = datetime.datetime.now() #Getting timestamp
    print t1
    print ' The threshold scan step is %d [DAC]' %(step)
    print ' The channel to be tested is #%d'%(channel)

    print "----------threshold scan------------------------"
    LowerThresholdsToMin(PowerUnitID)
    RaiseThresholdsToMax(PowerUnitID)
    print 'Set Power voltage to %d [DAC]' %(Vset) 
    SetPowerVoltage(channel, Vset, PowerUnitID) 
    sleep(3)
    # print "-------enable all channel--------"
    #for ichannel in range(8):UnlatchPower(ichannel)
    UnlatchPower(channel, PowerUnitID)
    'Latch status is ' , bin(GetPowerLatchStatus(PowerUnitID)) 
    ConfigurePowerADC(PowerUnitID) #this is necessary to be able to read ADCs
    sleep(0.5)
    print "ch# Th[DAC] Vset [DAC] V [V] I [A]  R [ohm] T[C]"
    print ' Threshold scan loop ' 
    for thvalue in range(start,end, -1*step): 
        threshold = (thvalue * 16) - 1 

        I, V, I_ADC, V_ADC = ReadPowerADC(PowerUnitID) #read current and voltage from ADCs (before setting new threshold)
        Iread = Vread = 0                   
        Vread = V[channel]
        Iread = I[channel]
	rload = -1
	if(Iread>0): rload = Vread/Iread
        Vread_ADC = V_ADC[channel]
        Iread_ADC = I_ADC[channel]
 	T = ReadRTD(PowerUnitID)
        line = "%d %5d %5d %10.2f %8.2f %8.2f %8.2f" % (channel, threshold, Vset, Vread, Iread, rload, T)
        print line
        SetThreshold(channel, threshold, PowerUnitID)

        LUstate = GetPowerLatchStatus(PowerUnitID)
        if ((int(LUstate) & 2**channel) != 2**channel):
            print "!!!!!!!!!!!!!!Channel %d latched!!!!!!!!!!" %(channel)
            with open(output,"ab") as f:
                f.write(str(line) + "\n")
                break # break the threshold loop
            if (LUstate == 0xff):
                break #break the threshold loop
            print '\n'
    LowerThresholdsToMin(PowerUnitID)
    RaiseThresholdsToMax(PowerUnitID)                
    DisablePowerAll(PowerUnitID)
    CloseFtdi()
    print 'End of the threshold scan function,'
    return 



   
