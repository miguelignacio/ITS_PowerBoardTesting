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
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from definitions import ReadRSFromDeviceToArray

from UsefulFunctions import *
# scan definition MSByte
stop = 10
start = 255
#step = 50
#Vlist = [125] #, 100, 225]

def thresholdScanAll(output,master, channel, step, Vset):
    print 'Entering function threshold scan, '
    LUstate = 0          
    startime = time.strftime("%Y-%m-%d_%H-%M-%S") #Setting timestamp format 
    t1 = datetime.datetime.now() #Getting timestamp
    print t1
    # Vout loop
    print ' The threshold scan step is %d [DAC]' %(step)
    print ' The channel to be tested is #%d'%(channel)

    print "----------threshold scan------------------------"
    RaiseThresholdsToMax()
    print "----------set mid-range output for all channels ---------------"
    for ichannel in range(8): SetVoltage(master, ichannel, Vset) #loops over all channels and sets voltage
    print "-------enable all channel--------"
    for ichannel in range(8): Unlatch(master, ichannel)

    'Latch status is ' , PrintLatchStatus(master)
    AddressConfigRegADC(master) #this is necessary to be able to read ADCs
    sleep(0.1)
    print ' Threshold scan loop ' 
    for thvalue in range(start,stop, -1*step): 
        #read IV 
        thvalueAmps = thvalue*0.01028-0.104 #this calibration
        print '----------Reading I,V---------- ' 
        I, V, I_ADC, V_ADC = ReadADC(master) #read current and voltage from ADCs (before setting new threshold)
        Iread = Vread = 0                   
        #Looping over channels, printing the saved currents and voltages. These are the last ones before latch occurred
        Vread = V[channel]
        Iread = I[channel]
        #print 'Voltage' , Vread , ' current ' , Iread
	rload = -1
	if(Iread>0): rload = Vread/Iread
        Vread_ADC = V_ADC[channel]
        Iread_ADC = I_ADC[channel]
 	 
        line = "%d %5d %10.3f %5d %10.2f %8.2f %8.2f %8.d %4.d %4.d" % (channel, thvalue, thvalueAmps, Vset, Vread, Iread, rload, start, stop, step)
        print "ch# Vset [DAC] V [V] I [A]  R [ohm]"
        print "%d %5d %10.2f %8.2f %8.2f" % (channel, Vset, Vread, Iread, rload)
        #print I
        # Set Threshold
        print "----------Set new threshold------------"
        print "Thresholds = %d [DAC] = %.3f [A]" %(thvalue, thvalueAmps)      
        #for ichannel in range(8):
        SetThreshold(master, channel, thvalue)
        # print LU state
        print "----------Read latch-up state------------"
        LUstate = PrintLatchStatus(master)
            
        if ((LUstate & 2**channel) == 2**channel):
            print "!!!!!!!!!!!!!!Channel %d latched!!!!!!!!!!" %(channel)
            with open(output,"ab") as f:
                f.write(str(line) + "\n")
                break # break the threshold loop
            if (LUstate == 0xff):
                break #break the threshold loop
            print '\n'
                    
    LowerThresholdsToMin() #set the thresholds super low to be able to latch them all 
    print 'End of the threshold scan function,'
    return #end of function



   
