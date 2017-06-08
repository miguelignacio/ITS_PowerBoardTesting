#!/usr/bin/python

import Tkinter as tk
import tkMessageBox

import os
import io
import sys
import time
import subprocess
import json
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
from I2CTest import I2C
from SetThreshold import SetThresh

from VoltageScan import *
from ThresholdScan import *
from TemperatureTest import* 
from LatchStatusCheck import *
import PowerboardTestData as PbData


outputFolder = 'TXTFILES/'
configurationFolder = 'LargeScaleTest/ScanConfig/'

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(ipadx = 10, ipady = 10)

        frame = tk.Frame(master)
        frame.grid()

        config = {}

        # get the most recent configuration file
        files = os.listdir(configurationFolder)
        prefix = 'config'
        numbers = [int(f[len(prefix):]) for f in files if f.startswith(prefix) and not f.endswith('~')]
        configNumber = max(numbers)
        configurationFile = configurationFolder + prefix + str(configNumber)

        with open(configurationFile) as f:
            config = json.load(f)

        self.test_names= ["CH#%i"%n for n in range(16)]
        self.boxes = []
        self.Eboxes = []
        self.box_vars = []
        self.box_enab = []
        self.box_num = 0
        self.BOARD_ID=1


        def buildOutputFilename(timestamp, testName):
          filename = outputFolder + str(timestamp)
          filename = filename +'_BoardID%i_PowerUnitID%s_LoadType%s_Config%s_%s_%s.txt' %(GetBoardID(), GetPowerUnitID(), GetLoadType(), configNumber, testName, GetNameOfTester())
          return filename


        #MAIN FUNCTION:
        ch_vars = [0 for i in range(16)]
        ch_en = [0 for i in range(16)]

       
        PowerUnitID = tk.IntVar()

        tk.Label(self, text = "Power unit #1").grid(row = 0, column = 1)
        tk.Label(self, text = "      ").grid(row = 0, column = 0)
        tk.Label(self, text = "Power unit #2").grid(row = 1, column = 1)
        M = tk.Radiobutton(self, variable=PowerUnitID, value=1)
        S = tk.Radiobutton(self, variable=PowerUnitID, value=2)
        M.grid(row = 0, column = 2)
        S.grid(row = 1, column = 2)
        PowerUnitID.set(1)

        def GetPowerUnitID():
	    return PowerUnitID.get()

        NameOfTester = tk.IntVar()

        def GetBoardID():
            print 'The board ID is ' , self.BOARD_ID
            return self.BOARD_ID

        ############# SHOWS BOARD ID ##############################################
        tk.Label(self, text = "Board ID = ?", bg='red', fg="blue").grid(row = 0, column = 9)
        def LabelBoardID():
            tk.Label(self, text = "Board ID = %i" %(int(GetBoardID())), bg='green', fg="blue").grid(row = 0, column = 9)

        def ScanBoardID(): #to be implemented with barcode.
            self.BOARD_ID =int(raw_input('Please read barcode on board...'))
            LabelBoardID()

            return
        ScanID = tk.Button(self, text="Scan Board ID", command = ScanBoardID)
        ScanID.grid(row = 0, column = 10, columnspan = 4)

        ################################################################################################
        ############ SETTING NAME
        NameOfTester = tk.IntVar()
        tk.Label(self, text = "Pick your name", fg="red").grid(row = 18, column = 10)
        tk.Label(self, text = "Fernando").grid(row = 19, column = 10)
        tk.Label(self, text = "Joshua").grid(row = 20, column = 10)
        tk.Label(self, text = "Miguel").grid(row = 21, column = 10)
        tk.Radiobutton(self, variable=NameOfTester, value=1).grid(row = 19, column = 12)
        tk.Radiobutton(self, variable=NameOfTester, value=2).grid(row = 20, column = 12)
        tk.Radiobutton(self, variable=NameOfTester, value=3).grid(row = 21, column = 12)

        def GetNameOfTester():
            name_id = NameOfTester.get()
            name = 'Unknown'
            if(name_id==1): return 'Fernando'
            elif(name_id==2): return 'Joshua'
            elif(name_id==3): return 'Miguel'
            return 'Unknown'
  
        ################################################################################################
        ######## PICK TYPE OF LOAD #####################################################################
        #################################################################################################
        LoadType = tk.IntVar()
        tk.Label(self, text = "Pick load type used", fg="red").grid(row = 8, column = 10)
        tk.Label(self, text = "#1 (nominal)").grid(row = 9, column = 10)
        tk.Label(self, text = "#2 (low power)").grid(row = 10, column = 10)
        tk.Label(self, text = "#3 (high power)").grid(row = 11, column = 10)

        tk.Radiobutton(self, variable=LoadType, value=1).grid(row = 9, column = 12)
        tk.Radiobutton(self, variable=LoadType, value=2).grid(row = 10, column = 12)
        tk.Radiobutton(self, variable=LoadType, value=3).grid(row = 11, column = 12)
        LoadType.set(1)
        def GetLoadType():
            load_id = LoadType.get()
            load = 'Unknown'
            if(load_id==1): return '1'
            elif(load_id==2): return '2'
            elif(load_id==3): return '3'
            return 'Unknown'

        ################################################################################################
        ######## SELECT VOLTAGE SCAN PLOTTING OPTION ###################################################
        #################################################################################################
        VoltageScanPlotOption = tk.IntVar()
        tk.Label(self, text = "Plot voltage scan results?").grid(row = 28, column = 10)
        tk.Label(self, text = "Slopes only").grid(row = 29, column = 10)
        tk.Label(self, text = "Slopes and fit").grid(row = 30, column = 10)
        # tk.Label(self, text = "Do not plot").grid(row = 31, column = 10)

        tk.Radiobutton(self, variable=VoltageScanPlotOption, value=1).grid(row = 29, column = 12)
        tk.Radiobutton(self, variable=VoltageScanPlotOption, value=2).grid(row = 30, column = 12)
        # tk.Radiobutton(self, variable=VoltageScanPlotOption, value=3).grid(row = 31, column = 12)
        # Plot slopes by default
        VoltageScanPlotOption.set(2)


        def RunI2CTest(timestamp=time.strftime("%Y%m%dT%H%M%S")):
            #tkMessageBox.showwarning( "Info", "All tests finished. If you have any comment please enter it below", icon="info")
            I2C()

        def RunThresholdScan(timestamp=time.strftime("%Y%m%dT%H%M%S")):
            if( not AreSelectedChannels()): return
            print ' Running the threshold scan'
            #timestamp =  time.strftime("%Y%m%dT%H%M%S") #Setting timestamp format
            output = buildOutputFilename(timestamp, "ThresholdScan")
            step = config["ThresholdScan_Thstep"]
            start = config["ThresholdScan_start"]
            end = config["ThresholdScan_end"]
	    Vset = config["ThresholdScan_Vpoints"]
	    print 'Vset ' , Vset

            if os.path.exists(output): # Delete data file with this name if found
                os.remove(output)
            header = "ch# Threshold[DAC] Vset [DAC] V [V] I [A]  R [ohm] T[C]"
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
            for x in range(0,16):
                ch_vars[x] = self.box_vars[x].get()
                if(ch_vars[x] == 1):
                        for V in Vset:
                            thresholdScanAll(output,x, step, start , end, V, PowerUnitID.get())
            print 'Threshold scan test ended. Output written in: ', output

        def RunPowerVoltageScan(timestamp=time.strftime("%Y%m%dT%H%M%S")):
            #if( not AreSelectedChannels()): return
            print ' Running power voltage scan '
            output = buildOutputFilename(timestamp, "VoltageScan")
            Vstep = config["PowerScan_Vstep"]
            start = config["PowerScan_start"]
            end = config["PowerScan_end"]
            samplingtime = config["PowerScan_samplingtime"]
            nsamples = config["PowerScan_nsamples"]
            sleep = config["PowerScan_sleep"]
            if os.path.exists(output): os.remove(output) # Delete data file with this name if found
            header ="#ch Vset [DAC] V [V] VRMS [mV] dV[mV] I [A] IRMS [mA] dI [mA] R [ohm] T[C] LUstate"
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
            #for ichannel in range(0, 16):
            #    ch_vars[ichannel] = self.box_vars[ichannel].get()
            #    if(ch_vars[ichannel] == 1 ):
            PowerVoltageScan(output, Vstep, start, end, samplingtime, nsamples, sleep, PowerUnitID.get())
            print 'Voltage scan test ended. Results were written in: ', output

            vsData = PbData.VoltageScan() #commented because I broke it adding new things
            vsData.readFile(output)

            plotOption = VoltageScanPlotOption.get()
            vsHasProblem = False
            if (plotOption == 1):
               vsHasProblem = vsData.visualizeAndCheck()
            elif (plotOption == 2):
               vsHasProblem = vsData.visualizeAndCheck(True)
            #do nothing otherwise


        def RunBiasVoltageScan(timestamp=time.strftime("%Y%m%dT%H%M%S")):
         
            print ' Running bias voltage scan '
            output = buildOutputFilename(timestamp, "BiasVoltageScan")
            isMaster = True
            Vstep = config["BiasScan_Vstep"]
            start = config["BiasScan_start"]
            end = config["BiasScan_end"]
            sleep = config["BiasScan_sleep"]
            samplingtime = config["BiasScan_samplingtime"]
            nsamples = config["BiasScan_nsamples"]

            if os.path.exists(output): os.remove(output) 
            header = "Vset [DAC] V [V] VRMS [V] dV[mV] I [A] IRMS [A] dI[mA] R [ohm] T[C]"
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
            BiasVoltageScan(output, Vstep, start, end, samplingtime, nsamples, sleep, PowerUnitID.get())
            print 'Voltage scan test ended. Results were written in: ', output       

        def RunOverTprotectionScan(timestamp=time.strftime("%Y%m%dT%H%M%S")):
            print ' Running temperature scan '
            output = buildOutputFilename(timestamp, "TemperatureScan")
            if os.path.exists(output): os.remove(output)
            header = "Vavg [V] Itot [A] T [C]"
            with open(output,"ab") as f:
                f.write(str(header) + "\n")

            timestep = config["TemperatureScan_timestep"]
            Vset = config["TemperatureScan_Vset"]

            Tlast = TemperatureTest(output, timestep, PowerUnitID.get(), Vset)
            print 'Temperature scan ended. The last temperature measured is %f. Results were written in: %s' %(Tlast,output)      


        def RunLatchupCheck(timestamp=time.strftime("%Y%m%dT%H%M%S")):
            print ' Running latchup check scan '
            output = buildOutputFilename(timestamp, "LachupTest")
            if os.path.exists(output): os.remove(output)
            header = "#ch Before Enabling / After Enabling / After Latching"
            with open(output,"ab") as f:
                f.write(str(header) + "\n")
            sleep = config["LatchTest_sleep"]		
            LatchUpCheck(output, sleep, PowerUnitID.get())
            print 'Latchup check ended. Results were written in %s' %(output)

        def AreSelectedChannels():
            flag = False
            for x in range(0, 16):
                ch_vars[x] = self.box_vars[x].get()
                if(ch_vars[x] == 1) : 
                    flag = True
            if not flag:
                tkMessageBox.showwarning("", "Please select a channel to scan")
            return flag

        def RunAllScans():
            if tkMessageBox.askyesno( "", "Did you do visual inspection & smoke test?"):
                if tkMessageBox.askyesno( "", "Is the following info OK? \n \n Board ID= %i \n Load array type= %s \n Your name= %s" 
                                               %(GetBoardID(), GetLoadType(), GetNameOfTester()) ):
                    timestamp =  time.strftime("%Y%m%dT%H%M%S") #Setting timestamp format
                    output = buildOutputFilename(timestamp, "VisualAndSmokeTest")
                    if os.path.exists(output): os.remove(output)
                    with open(output,"ab") as f: f.write("OK\n")
                    if tkMessageBox.askyesno( "", "Are you sure you want to run all tests?"):
                        if( not AreSelectedChannels()): return
                        #RunI2CTest(timestamp)
	                RunLatchupCheck(timestamp)
                        RunOverTprotectionScan(timestamp)
                        RunBiasVoltageScan(timestamp)
                        RunThresholdScan(timestamp)
                        RunPowerVoltageScan(timestamp)

                        tkMessageBox.showwarning( "Info", "All tests finished. If you have any comment please enter it below", icon="info")
            return

        def SetVoltage():
            voltage = vtext.get()
            for x in range(0, NofChannels()):
                ch_vars[x] = self.box_vars[x].get()
                if(ch_vars[x]==1):
                    SetVoltage(x, voltage)

        def SetComment():
            myComment = Comment.get()
            if tkMessageBox.askyesno( "", "Do you want to enter the following comment: \n \n '%s ' \n made by: %s" %(myComment, GetNameOfTester())):
                print myComment
            return

        def SetThreshVal():
            thresh = ttext.get()
            if len(ttext.get())==0:
                thresh = 0
            if (int(thresh) < 0 or int(thresh) > 255):
                tkMessageBox.showwarning("", "Threshold value must be between 0-255")
            for x in range(0, NofChannels()):
                ch_vars[x] = self.box_vars[x].get()
                if(ch_vars[x] == 1):
                    SetThreshold(x, thresh)

        ####SETTING THE CHANNELS BOXES####################################################################
        for index, name in enumerate(self.test_names):
            ROW = 5
            if index>7: ROW=6
            self.box_vars.append(tk.IntVar())
            self.boxes.append(tk.Checkbutton(self, text = name, variable = self.box_vars[self.box_num]))
            self.boxes[self.box_num].grid(row = ROW, column = (self.box_num)%8)
            self.box_num += 1
        ################################################################################################

        ### I2C ###########################################################
        I2CButton = tk.Button(self, text="I2C Test", command = RunI2CTest)
        I2CButton.grid(row = 0, column = 6, columnspan = 2)
        ###################################################################


        ######### VOLTAGE SCAN ###################################################################
        RUN = tk.Button(self, text="Power scan", command = RunPowerVoltageScan)
        RUN.grid(row = 10, column = 0, columnspan = 3)
        ###########################################################################################

        ######### BIAS VOLTAGE SCAN ###################################################################
        BiasVoltageScanButton = tk.Button(self, text="Bias scan", command = RunBiasVoltageScan)
        BiasVoltageScanButton.grid(row = 12, column = 1, columnspan = 3)
        ###########################################################################################


        ###########THRESHOLD SCAN########################################
        ThresholdScanButton = tk.Button(self, text = "Threshold scan", command = RunThresholdScan)
        ThresholdScanButton.grid(row=10, column = 2, columnspan =3)
        #############################################################################

        ###########TEMPERATURE SCAN########################################
        TemperatureButton = tk.Button(self, text = "Temperature scan", command = RunOverTprotectionScan)
        TemperatureButton.grid(row=12, column = 3, columnspan =4)
        ##########################################################################################

        ###########LATCH STATUS CHECK########################################
        TemperatureButton = tk.Button(self, text = "Latchup scan", command = RunLatchupCheck)
        TemperatureButton.grid(row=10, column = 4, columnspan =4)
        ##########################################################################################

        

        ########## ENTER COMMENT #############################################################
        Comment = tk.StringVar()
        CommentWant = tk.Entry(self, textvariable=Comment)
        CommentWant.grid(row = 22, column = 0, columnspan = 10)
        SETCOMMENT = tk.Button(self, text="Enter your Comment", command = SetComment)
        SETCOMMENT.grid(row = 21, column = 0, columnspan = 10)
        ######################################################################################


        ### Run all test ##################################################################
        RunAllTestsButton = tk.Button(self, text="Run All Tests", command = RunAllScans, bg='red')
        RunAllTestsButton.grid(row = 25, column = 1, columnspan = 7)
        ###################################################################################


##Actual MAIN FUNCTION
root = tk.Tk()
app = Application(master=root)
app.mainloop()

