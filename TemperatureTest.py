#!/usr/bin/python
import time

from UsefulFunctions import *


def TemperatureTest(output, timestep=0.5, PowerUnitID=1, Vset=125):

    startime = time.strftime("%Y%m%d%H%M%S") #Setting timestamp format
    t = datetime.datetime.now() #Getting timestamp
    print t
    OpenFtdi()

    ConfigureRTD(PowerUnitID) #configure RTD to be able to read it
    LowerThresholdsToMin(PowerUnitID) #to latch everything and erase whatever previous state
    RaiseThresholdsToMax(PowerUnitID) #to avoid latching
    SetPowerVoltageAll(Vset, PowerUnitID) #set power voltage
    print 'Latch status is ' , GetPowerLatchStatus(PowerUnitID)
    UnlatchPowerAll(PowerUnitID)# unlatch all channels
    ConfigurePowerADC(PowerUnitID) # configure power ADC to be able to read currents 
    time.sleep(1)
    time.sleep(0.5) 
    Triggered = False
  
    while not Triggered:
        T = ReadRTD(PowerUnitID)
        #print "Temperature %f" %(T)
        I, V, I_ADC, V_ADC = ReadPowerADC(PowerUnitID)
        #print I
        #print 'Itotal =%f' %(sum(I))
        #print 'Vavg  =%f' %(sum(V)/len(V))
	
        Itot = sum(I)
        Vavg = sum(V)/len(V)
        time.sleep(timestep)
        
        #line = "%8.5f %8.5f %8.5f" % (Vavg, Itot, T)
        #print "Vavg [V] Itot [A] T [C]"
	#print I
        print "%8.5f %8.5f %8.5f " % (Vavg, Itot, T)  
   
        LUstate = GetPowerLatchStatus(PowerUnitID)
       
        #if Itot<0.1 or LUstate==0x00 or Vavg<0.1:
	if Vavg < 0.001:
            Triggered = True
	else:
	    line = "%8.5f %8.5f %8.5f %s" % (Vavg, Itot, T, str(bin(LUstate)) )
            print "Vavg [V] Itot [A] T [C] LUstate"
            print line
	    Tlast = T  

    with open(output,"ab") as f:
        f.write(str(line) + "\n")
    LowerThresholdsToMin(PowerUnitID)
    DisablePowerAll(PowerUnitID)
    CloseFtdi()
    return Tlast
