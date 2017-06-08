#!/usr/bin/env python

import PowerboardTestDB as db
import ROOT
from array import array


class _VoltageScanStep(object):
	def __init__(self, vsetDac, v, vrms, dv, i, irms, di, r, t):
		self.VsetDAC = vsetDac
		self.V = v
		self.Vrms = vrms
		self.dV = dv
		self.I = i
		self.Irms = irms
		self.dI = di
		self.R = r
		self.T = t


class VoltageScan(object):
	def __init__(self):
		self.ChannelData = {}

	def readFile(self, filename):
		# #ch Vset [DAC] V [V] VRMS [mV] dV[mV] I [A] IRMS [mA] dI [mA] R [ohm] T[C]
		with open(filename) as f:
			for line in f:
				data = line.split()
				if len(data) == 10 and data[0].isdigit():
					channelNumber = data[0]

					if channelNumber not in self.ChannelData:
						self.ChannelData[channelNumber] = []

					self.ChannelData[channelNumber].append(_VoltageScanStep(data[1],data[2],data[3],data[4],data[5],data[6],data[7], data[8], data[9]))			


	def readDB(self, boardNumber, testId=0):
		rows = db.getRows("VoltageScan", boardNumber, testId)
		for row in rows:
			channelNumber = row["ChannelNumber"]

			if channelNumber not in self.ChannelData:
				self.ChannelData[channelNumber] = []

			self.ChannelData[channelNumber].append(_VoltageScanStep(row["VsetDAC"], row["V"], row["Vrms"], row["dV"], row["I"], row["Irms"], row["dI"], row["R"], row["T"]))


	def visualizeAndCheck(self, showFits=False):
		hasProblem = False

		# setting up all of the arrays
		channels, vints, vslopes, islopes = array('f'), array('f'), array('f'), array('f')
		channelserr, vintserr, vslopeserr, islopeserr = array('f'), array('f'), array('f'), array('f')
		fitgraphs = []

		# a rather ugly way of getting the number of bins
		nSteps = len(self.ChannelData.values()[0])
		vrms = ROOT.TH2F("vrms", "V RMS", nSteps, 0, 256, 16, 0, 16)
		irms = ROOT.TH2F("irms", "I RMS", nSteps, 0, 256, 16, 0, 16)

		for channelNumber, steps in self.ChannelData.iteritems():
			channels.append(float(channelNumber))
			channelserr.append(0.0)

			# pulling relevant data
			dac, v, i = array('f'), array('f'), array('f')

			for step in steps:
				dac.append(float(step.VsetDAC))
				v.append(float(step.V))
				i.append(float(step.I))
				
				bin = vrms.FindBin(float(step.VsetDAC), float(channelNumber))
				vrms.SetBinContent(bin, 1000*float(step.Vrms))
				irms.SetBinContent(bin, 1000*float(step.Irms))

			# creating and fitting each graph
			vgraph, vfit = self._createAndFitGraph(dac, v, int(channelNumber)%8)
			vslopes.append(vfit.GetParameter(1))
			vslopeserr.append(vfit.GetParError(1))
			vints.append(vfit.GetParameter(0))
			vintserr.append(vfit.GetParError(0))

			igraph, ifit = self._createAndFitGraph(i, v, int(channelNumber)%8)
			islopes.append(ifit.GetParameter(1))
			islopeserr.append(ifit.GetParError(1))

			fitgraphs.append((vgraph, igraph))

		if showFits:
			datacanvas = ROOT.TCanvas("datacanvas", "Data and fits")
			datacanvas.Divide(1,2)

			vmultigraph, imultigraph = ROOT.TMultiGraph(), ROOT.TMultiGraph()
			for graphs in fitgraphs:
				vmultigraph.Add(graphs[0])
				imultigraph.Add(graphs[1])

			datacanvas.cd(1)
			vmultigraph.Draw("ap")
			vmultigraph.GetXaxis().SetTitle("VsetDAC")
			vmultigraph.GetYaxis().SetTitle("V")
			datacanvas.cd(2)
			imultigraph.Draw("ap")
			imultigraph.GetXaxis().SetTitle("I")
			imultigraph.GetYaxis().SetTitle("V")

		fitcanvas = ROOT.TCanvas("fitcanvas", "Fit results")
		fitcanvas.Divide(3,1)

		fitcanvas.cd(1)
		vintsgraph = ROOT.TGraphErrors(len(channels), channels, vints, channelserr, vintserr)
		vintsgraph.SetTitle("Intercept [V]")
		vintsgraph.SetMarkerStyle(4)
		vintsgraph.GetXaxis().SetLimits(-1,17)
		hasProblem = self._checkAndDraw(vintsgraph, vints, 0.1) or hasProblem

		fitcanvas.cd(2)
		vslopesgraph = ROOT.TGraphErrors(len(channels), channels, vslopes, channelserr, vslopeserr)
		vslopesgraph.SetTitle("Slope V vs DAC")
		vslopesgraph.SetMarkerStyle(4)
		vslopesgraph.GetXaxis().SetLimits(-1,17)
		hasProblem = self._checkAndDraw(vslopesgraph, vslopes, 0.1) or hasProblem

		fitcanvas.cd(3)
		islopesgraph = ROOT.TGraphErrors(len(channels), channels, islopes, channelserr, islopeserr)
		islopesgraph.SetTitle("Load [#Omega]")
		islopesgraph.SetMarkerStyle(4)
		islopesgraph.GetXaxis().SetLimits(-1,17)
		islopesgraph.Draw("ap")

		rmscanvas = ROOT.TCanvas("rmscanvas", "RMS measurements")
		rmscanvas.Divide(2,1)
		rmscanvas.cd(1)
		vrms.Draw("COLZ")
		rmscanvas.cd(2)
		irms.Draw("COLZ")

		raw_input("Press enter to continue")

		return hasProblem


	def _createAndFitGraph(self, x, y, color):
		graph = ROOT.TGraph(len(x), x, y)
		graph.Fit('pol1', 'q')
		fit = graph.GetFunction('pol1')
		graph.SetMarkerStyle(4)
		graph.SetMarkerColor(color)
		fit.SetLineColor(color)
		return (graph, fit)


	def _checkAndDraw(self, graph, values, tolerance):
		graph.Draw("ap")
		graph.Fit('pol0', 'q0')
		fit = graph.GetFunction('pol0')
		center = fit.GetParameter(0)
		graphMin = (1-tolerance)*center
		graphMax = (1+tolerance)*center

		exceedsRange = False
		for value in values:
			if value > graphMax or value < graphMin:
				exceedsRange = True

		if exceedsRange:
			# draw dashed horizontal lines indicating the tolerance
			# actually, turn everything red, because ROOT is a pain
			graph.SetMarkerColor(2)
			graph.SetMarkerStyle(20)
			graph.SetLineColor(2)
			graph.SetFillColor(2)
		else:
			# rescale the axes
			graph.SetMinimum(graphMin)
			graph.SetMaximum(graphMax)
		
		return exceedsRange


class BiasVoltageScan(object):
	def __init__(self):
		self.Data = []

	def readFile(self, filename):
		# Vset [DAC] V [V] VRMS [V] dV[mV] I [A] IRMS [A] dI[mA] R [ohm] T[C]
		with open(filename) as file:
			for line in file:
				data = line.split()
				if len(data) == 9 and data[0].isdigit():
					self.Data.append(_VoltageScanStep(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8]))

	def readDB(self, boardNumber, testId=0):
		rows = db.getRows("BiasVoltageScan", boardNumber, testId)
		for row in rows:
			self.Data.append(_VoltageScanStep(row["VsetDAC"], row["V"], row["Vrms"], row["dV"], row["I"], row["Irms"], row["dI"], row["R"], row["T"]))


class _ThresholdScanStep(object):
	def __init__(self, thDac, thA, vsetDac, vmon, imon, r, start, end, step):
		self.ThDAC = thDac
		self.ThA = thA
		self.VsetDAC = vsetDac
		self.Vmon = vmon
		self.Imon = imon
		self.R = r
		self.Start = start
		self.End = end
		self.Step = step


class ThresholdScan(object):
	def __init__(self):
		self.ChannelData = {}

	def readFile(self, filename):
		with open(filename) as f:
			for line in f:
				data = line.split()
				if len(data) >= 10 and data[0].isdigit():
					channelNumber = data[0]

					if channelNumber not in self.ChannelData:
						self.ChannelData[channelNumber] = []

					self.ChannelData[channelNumber].append(_ThresholdScanStep(data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9]))


	def readDB(self, boardNumber, testId=0):
		rows = db.getRows("ThresholdScan", boardNumber, testId)
		for row in rows:
			channelNumber = row["ChannelNumber"]

			if channelNumber not in self.ChannelData:
				self.ChannelData[channelNumber] = []

			self.ChannelData[channelNumber].append(_ThresholdScanStep(row["ThDAC"], row["ThA"], row["VsetDAC"], row["Vmon"], row["Imon"], row["R"], row["Start"], row["End"], row["Step"]))


class TestInfo(object):
	def __init__(self):
		pass

	def parseFilename(self, filename):
		metadata = filename.split("_")

		self.Timestamp = metadata[0]
		# strip off "BoardID"
		self.BoardNumber = metadata[1][7:]
		# strip off "PowerUnitID"
		self.PowerUnit = metadata[2][11:]
		# strip off "LoadType"
		self.LoadType = metadata[3][8:]
		# strip off "Config"
		self.Config = metadata[4]
		# strip off ".txt"
		self.Tester = metadata[6][:-4]


	def readDB(self, boardNumber, testId=0):
		row = db.getRows("TestInfo", boardNumber, testId)[0]
		self.Id = row["Id"]
		self.BoardNumber = row["BoardNumber"]
		self.TestNumber = row["TestNumber"]
		self.LoadType = row["LoadType"]
		self.PowerUnit = row["PowerUnit"]
		self.Config = row["Config"]
		self.Tester = row["Tester"]
		self.Timestamp = row["Timestamp"]
