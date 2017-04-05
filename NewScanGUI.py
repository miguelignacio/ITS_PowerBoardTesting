#!/usr/bin/python

import Tkinter as tk
import tkMessageBox

import os
import io
import sys
import time
import subprocess
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from ScanVI import SetCh
from ScanVI import enable
#from ScanAll import ScanAllCH
from SetVoltage import SetV
from I2CAddressability import I2C
from BiasCheck import BiasScan
from SetThreshold import SetThresh

from VoltageScan import VoltageScan
from ThresholdScan import *


outputFolder = 'TXTFILES/'

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(ipadx = 10, ipady = 10)

	frame = tk.Frame(master)
        frame.grid()
        #f2 = tk.Frame(master,width=100,height=300)
        #f2.grid(row=1,column=1)

        self.test_names = ["CH 0", "CH 1", "CH 2", "CH 3", "CH 4", "CH 5", "CH 6", "CH 7"]
        self.boxes = []
	self.Eboxes = []
        self.box_vars = []
        self.box_enab = []
        self.box_num = 0

        #MAIN FUNCTION: 
	ch_vars = [0 for i in range(8)]
	ch_en = [0 for i in range(8)]

        #########THIS BLOCK CREATES a buttom to select master/slave. The variable is saved in "VAR"
	var = tk.IntVar()

	tk.Label(self, text = "Master").grid(row = 0, column = 1)
	tk.Label(self, text = "      ").grid(row = 0, column = 0)
	tk.Label(self, text = "Slave").grid(row = 1, column = 1)
	M = tk.Radiobutton(self, variable=var, value=0)
	S = tk.Radiobutton(self, variable=var, value=1)
	M.grid(row = 0, column = 2) 
	S.grid(row = 1, column = 2)


        ################################################################################################

        NameOfTester = tk.IntVar()
	tk.Label(self, text = "WhoAmI").grid(row = 9, column = 7)
        tk.Label(self, text = "Fernando").grid(row = 10, column = 7)
	tk.Label(self, text = "Joshua").grid(row = 11, column = 7)
        tk.Label(self, text = "Miguel").grid(row = 12, column = 7)
	tk.Label(self, text = "...").grid(row = 13, column = 7)
	WhoAmI = tk.Radiobutton(self, variable=NameOfTester, value=0)
	Fernando = tk.Radiobutton(self, variable=NameOfTester, value=1)
	Joshua = tk.Radiobutton(self, variable=NameOfTester, value=2)
        Miguel = tk.Radiobutton(self, variable=NameOfTester, value=3)
	Other = tk.Radiobutton(self, variable=NameOfTester, value=4)


        WhoAmI.grid(row = 9, column = 8) 
	Fernando.grid(row = 10, column = 8) 
	Joshua.grid(row =11, column = 8)
        Miguel.grid(row = 12, column = 8) 
	Other.grid(row =13, column = 8)

        def  GetNameOfTester():
	    name_id = NameOfTester.get()
	    name = 'Unknown'
	    if(name_id==1): return 'Fernando'
	    elif(name_id==2): return 'Joshua'
	    elif(name_id==3): return 'Miguel'
	    elif(name_id==4): return 'Other'
            elif(name_id==0): return 'WhoAmI'
	    return 

 	def I2CTest():
		I2C()
        
        def RunThresholdScan():
            if( not AreSelectedChannels()): return
            print ' Running the threshold scan' 
	    timestamp =  time.strftime("%Y%m%dT%H%M%S") #Setting timestamp format 
	    output = outputFolder+ str(timestamp) + '__ThresholdScan__'+ GetNameOfTester() +'.txt'
	    isMaster = True
            Vset = [125]
            Step = ScanStep.get()
            if len(ScanStep.get())==0:
                Step = 20
            if os.path.exists(output): # Delete data file with this name if found
                os.remove(output)
            header = "ch# Th[DAC] Th [A] Vset [DAC] Vmon [V] Imon [A]  R [ohm]   start end step "
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
	    for x in range(0, 8):
	        ch_vars[x] = self.box_vars[x].get()
	        if(ch_vars[x] == 1):
                    for V in Vset:	
                        thresholdScanAll(output, isMaster, x, int(Step), int(V))
            print 'Threshold scan test ended '
 
	def RunVoltageScan():
            if( not AreSelectedChannels()): return
	    print ' Running voltage scan '
            timestamp =  time.strftime("%Y%m%dT%H%M%S") #Setting timestamp format 
	    output = outputFolder+ str(timestamp) + '__VoltageScan__'+ GetNameOfTester() +'.txt'
	    isMaster = True
            step_size = step.get() 
            if len(step.get())==0:
                step_size = 10
            if os.path.exists(output): os.remove(output) # Delete data file with this name if found
            header = "ch# Vset [DAC] Vmon [V] Imon [A]  R [ohm] start end step "
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
	    for ichannel in range(0, 8):
	        ch_vars[ichannel] = self.box_vars[ichannel].get()
	        if(ch_vars[ichannel] == 1):
	            VoltageScan(output, master, ichannel, int(step_size))
	    print 'Voltage scan test ended ' 
	    
   
        def AreSelectedChannels():
	    flag = False
	    for x in range(0, 8):
	        ch_vars[x] = self.box_vars[x].get()
		if(ch_vars[x] == 1) : flag = True
	    if not flag: 
                tkMessageBox.showwarning("", "Please select a channel to scan")
            return flag
     
        def RunAllScans():
	    if tkMessageBox.askyesno( "", "Did you do visual inspection & smoke test?"):
	        if tkMessageBox.askyesno( "", "Did you check that board ID and your name are correct?"):
                    if tkMessageBox.askyesno( "", "Are you sure you want to run all tests?"):
                        if( not AreSelectedChannels()): return
                        RunVoltageScan()
	                RunThresholdScan()
                        I2CTest()
            return 
	
  	def SetVoltage():
		MS = var.get()
		voltage = vtext.get()
		for x in range(0, 8):
			ch_vars[x] = self.box_vars[x].get()
	                if(ch_vars[x] == 1):	
				SetV(MS,x,voltage)

  	def SetThreshVal():
		MS = var.get()
		thresh = ttext.get()
		if len(ttext.get())==0:
                	thresh = 0
		flag = 0
		for x in range(0, 8):
			ch_vars[x] = self.box_vars[x].get()
			if(ch_vars[x] == 1):
				flag = 1

		if (int(thresh) < 0 or int(thresh) > 255):
			tkMessageBox.showwarning("", "Threshold value must be between 0-255")
           	elif flag==0:
                	tkMessageBox.showwarning("", "Please select a channel")
		else:
			SetThresh(MS,ch_vars,thresh)
	 		
	
        
	################################################################################################
        for name in self.test_names:
            self.box_vars.append(tk.IntVar())
            self.boxes.append(tk.Checkbutton(self, text = name, variable = self.box_vars[self.box_num]))
            self.boxes[self.box_num].grid(row = 5, column = (self.box_num))
            self.box_num += 1
        ################################################################################################

	### I2C ###########################################################
    	I2CButton = tk.Button(self, text="I2C Test", command = I2CTest)
        I2CButton.grid(row = 0, column = 6, columnspan = 2)
        ###################################################################


        ######### VOLTAGE SCAN ###################################################################
	RUN = tk.Button(self, text="Voltage scan", command = RunVoltageScan)
	RUN.grid(row = 8, column = 0, columnspan = 4)
        tk.Label(self, text = "Step size (def=10)").grid(row = 9, column = 0, columnspan = 4)
	step = tk.StringVar()
	SSize = tk.Entry(self, textvariable=step)
	SSize.grid(row = 10, column = 0, columnspan = 4)
        ###########################################################################################

        ###########THRESHOLD SCAN########################################
        ThresholdScanButton = tk.Button(self, text = "Threshold scan", command = RunThresholdScan)
	ThresholdScanButton.grid(row=8, column = 3, columnspan =4)
        tk.Label(self, text = "Step size (def=10)").grid(row = 9, column = 3, columnspan = 4)
        ScanStep = tk.StringVar()
        ScanStepWant = tk.Entry(self, textvariable=ScanStep)
        ScanStepWant.grid(row = 10, column = 3, columnspan = 4)
        #############################################################################



        ########## SET VOLTAGE ########################################
        vtext = tk.StringVar()
        VoltWant = tk.Entry(self, textvariable=vtext)
        VoltWant.grid(row = 20, column = 0, columnspan = 4)
	SETVOLT = tk.Button(self, text="Set Voltage", command = SetVoltage)
        SETVOLT.grid(row = 19, column = 0, columnspan = 4)	
        #####################################################################

        ########## SET THRESHOLD ############################################################# 
        ttext = tk.StringVar()
        ThreshWant = tk.Entry(self, textvariable=ttext)
        ThreshWant.grid(row = 20, column = 4, columnspan = 4)
	SETTHRESH = tk.Button(self, text="Set Threshold", command = SetThreshVal)
        SETTHRESH.grid(row = 19, column = 4, columnspan = 4)	
        ######################################################################################


        ### Run all test ##################################################################
    	RunAllTestsButton = tk.Button(self, text="Run All Tests", command = RunAllScans)
        RunAllTestsButton.grid(row = 12, column = 2, columnspan = 4)
        ###################################################################################


##Actual MAIN FUNCTION
root = tk.Tk()
app = Application(master=root)
app.mainloop()

