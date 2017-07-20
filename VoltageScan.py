#!/usr/bin/env python
__author__ = "M.Arratia"
__version__ = "2.0"
__status__ = "Prototype"


###work in progress###, 03/23/17
from UsefulFunctions import *

import numpy as np

def PowerVoltageScan(output, step, start, end, SamplingTime, Nsamples, sleep, PowerUnitID):
    print 'Power Unit ID' , PowerUnitID
    OpenFtdi() # Starts communication with RDO board
    ConfigureRTD(PowerUnitID) #engaging the over-temperature monitoring.	
    startime = time.strftime("%Y%m%d%H%M%S") #Setting timestamp format 
    t1 = datetime.datetime.now() #Getting timestamp
    print t1
    print ' The voltage scan step is %d [DAC]' %(step)
    LowerThresholdsToMin(PowerUnitID) #to latch everything and erase whatever previous state
    RaiseThresholdsToMax(PowerUnitID)
    print 'Latch status is ' , bin(GetPowerLatchStatus(PowerUnitID)) 
    UnlatchPowerAll(PowerUnitID)#
    print 'Latch status is ' , bin(GetPowerLatchStatus(PowerUnitID)) 
    ConfigurePowerADC(PowerUnitID) # this is necessary to be able to read ADCs
    time.sleep(1.0)
    print "#ch Vset [DAC] V [V] VRMS [mV] dV[mV] I [A] IRMS [mA] dI [mA] R [ohm] T[C]"
    for voltage in range(start, end , -1*step): #loop over voltages
	print 'Setting voltage of all channels to %f [V] and sleeping %f [s]' %(voltage, sleep)
        SetPowerVoltageAll(voltage, PowerUnitID) ##set power voltage to all.
        time.sleep(sleep)
        LUstate = GetPowerLatchStatus(PowerUnitID)
        if LUstate == 0x00: break
        Imatrix = np.zeros((Nsamples,16))
	Vmatrix = np.zeros((Nsamples,16))
        
        for n in range(Nsamples):
            time.sleep(SamplingTime)
            Itemp, Vtemp, I_ADC, V_ADC = ReadPowerADC(PowerUnitID)
	    Imatrix[n] = Itemp
	    Vmatrix[n] = Vtemp
            
        T = ReadRTD(PowerUnitID)
        for ch in range(16): #loop over 
	    Ipoints = np.array([x[ch] for x in Imatrix])
	    Vpoints = np.array([x[ch] for x in Vmatrix])
            Iread = Ipoints.mean()
	    IRMS  = 1000*Ipoints.std()
	    Vread = Vpoints.mean()
	    VRMS  = 1000*Vpoints.std()
            DeltaI = 1000*(Ipoints.max()-Ipoints.min())
	    DeltaV = 1000*(Vpoints.max()-Vpoints.min())
	    rload = -666
	    if(Iread>0): rload = Vread/Iread
            if Vread<0.01: break
            line = "%d %5d %8.4f %8.1f %8.1f %8.4f %8.1f %8.1f %8.3f %8.1f %s" % (ch, voltage, Vread, VRMS, DeltaV, Iread, IRMS, DeltaI, rload, T, str(bin(LUstate)))
        
            print line
            with open(output,"ab") as f:
                f.write(str(line) + "\n")
 	    ########end of loop over voltage###############   
    LowerThresholdsToMin(PowerUnitID) #set the thresholds super low to be able to latch them all 
    RaiseThresholdsToMax(PowerUnitID)
    print 'Latch status is ' , GetPowerLatchStatus(PowerUnitID)
    print '################################################## \n'
    DisablePowerAll(PowerUnitID)
	
    CloseFtdi() # Ends communication with RDO board
    return

def BiasVoltageScan(output, step, start, end, SamplingTime, Nsamples, sleep, PowerUnitID):
    print 'Power Unit ID' , PowerUnitID
    OpenFtdi() # Starts communication with RDO board
    ConfigureRTD(PowerUnitID) #engaging the over-temperature monitoring.	
    startime = time.strftime("%Y%m%d%H%M%S") #Setting timestamp format 
    t1 = datetime.datetime.now() #Getting timestamp
    print t1
    print ' The voltage scan step is %d [DAC]' %(step)
    print 'Setting Bias Voltage ' 
    SetBiasVoltage(0,PowerUnitID)
    print 'Bias latch status is ' , GetBiasLatchStatus(PowerUnitID) 
    UnlatchBiasAll(PowerUnitID)

    ConfigureBiasADC(PowerUnitID) # this is necessary to be able to read ADCs
    time.sleep(1)
    print "Vset [DAC] V [V] VRMS [V] dV[mV] I [A] IRMS [A] dI[mA] R [ohm] T[C]"
    for voltage in range(start, end , -1*step):
        SetBiasVoltage(voltage, PowerUnitID)
        time.sleep(sleep)
	#print '----------Reading I,V---------- ' 
        # Put a software sleep here (20 ms) before sampling the output voltages
        
        Ipoints = np.array([])
	Vpoints = np.array([])
        for n in range(Nsamples):
            time.sleep(SamplingTime)
	    Itemp, Vtemp = ReadBiasADC(PowerUnitID) #read current and voltage from ADCs (before setting new threshold)
            Ipoints = np.append(Ipoints, Itemp)
	    Vpoints = np.append(Vpoints, Vtemp)

        Iread = Ipoints.mean()
	IRMS  = 1000*Ipoints.std()
	Vread = Vpoints.mean()
	VRMS  = 1000*Vpoints.std()
        DeltaI = 1000*(Ipoints.max()-Ipoints.min())
	DeltaV = 1000*(Vpoints.max()-Vpoints.min())
        rload = -1
	if(Iread>0): rload = Vread/Iread

        T = ReadRTD(PowerUnitID)
        line = "%5d %8.4f %8.1f %8.1f %8.4f %8.1f %8.1f %8.1f %8.1f" % (voltage, Vread, VRMS, DeltaV, Iread, IRMS, DeltaI, abs(rload), T)
        print line

        with open(output,"ab") as f:
            f.write(str(line) + "\n")
 	########end of loop over voltage###############   
    print 'Latch status is ' , GetBiasLatchStatus(PowerUnitID) 
    print '################################################## \n'

    DisableBiasAll(PowerUnitID)
	
    CloseFtdi() # Ends communication with RDO board
    return







#VoltageScan("biasscan.txt", True, 0, 20)
