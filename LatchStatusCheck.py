
from UsefulFunctions import*
import math
def LatchUpCheck(output, sleep, PowerUnitID):
    OpenFtdi() # Starts communication with RDO board
    ConfigureRTD(PowerUnitID) #engaging the over-temperature monitoring.
    startime = time.strftime("%Y%m%d%H%M%S") #Setting timestamp format
    t = datetime.datetime.now() #Getting timestamp
    print t
    print 'Starting latchup test' 
    print 'Latch at the beggining is: ' , bin(GetPowerLatchStatus(PowerUnitID))
    print 'Raise Threshold of all channels to maximum' 
    LowerThresholdsToMin(PowerUnitID) #to latch everything and erase whatever previous state
    RaiseThresholdsToMax(PowerUnitID)
    #loop over channels
    for channel in range(16):
	print 'channel %d' %(channel)
        beforeEnabling = GetPowerLatchStatus(PowerUnitID)
        UnlatchPower(channel, PowerUnitID)#enable channel 
	time.sleep(sleep)
        afterEnabling = GetPowerLatchStatus(PowerUnitID) #read status
        SetThreshold(channel, 0, PowerUnitID) #set threshold of channel to zero to latch it
        time.sleep(sleep)
        afterLatching = GetPowerLatchStatus(PowerUnitID) #read status
        print '#ch Before Enabling / After Enabling / After Latching'
        line = "%d %5d %5d %5d" %(channel, beforeEnabling, afterEnabling, afterLatching)
	print line
        with open(output,"ab") as f:
            f.write(str(line) + "\n")
  
    DisablePowerAll(PowerUnitID)
    LowerThresholdsToMin(PowerUnitID) #to latch everything and erase whatever previous state
    RaiseThresholdsToMax(PowerUnitID)
    CloseFtdi() # Ends communication with RDO board
    return
