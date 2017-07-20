#!/usr/bin/env python

import PowerboardTestDB as db
import ROOT
from array import array


columns = {}
columns["ThresholdScan"] = ["ChannelNumber", "ThDAC", "VsetDAC", "V", "I", "R", "T", "LUState"]
columns["VoltageScan"] = ["ChannelNumber", "VsetDAC", "V", "Vrms", "dV", "I", "Irms", "dI", "R", "T", "LUState"]
columns["BiasVoltageScan"] = ["VsetDAC", "V", "Vrms", "dV", "I", "Irms", "dI", "R", "T"]
columns["TemperatureScan"] = ["Vavg", "Itot", "T"]
columns["LatchupTest"] = ["ChannelNumber", "BeforeEnabling", "AfterEnabling", "AfterLatching"]
columns["TestInfo"] = ["BoardNumber", "BoardVersion", "TestNumber", "LoadType", "PowerUnit", "Config", "Tester", "Timestamp"]


class Scan(object):
    def __init__(self, testName, hasChannelData):
        self.Data = []
        self.columns = columns[testName]
        self.testName = testName
        self.hasChannelData = hasChannelData

    def readFile(self, filename):
        with open(filename) as f:
            for line in f:
                data = line.split()
                if len(data) == len(self.columns) and data[0].isdigit():
                    self.Data.append(dict(zip(self.columns, data)))
        if self.hasChannelData:
            self.buildChannelData()

    def readDB(self, boardNumber, testId=0):
        self.Data = db.getRows(testName, boardNumber, testId)
        if self.hasChannelData:
            self.buildChannelData()

    def buildChannelData(self):
        self.ChannelData = {}

        for step in self.Data:
            channelNumber = step["ChannelNumber"]
            if channelNumber not in self.ChannelData:
                self.ChannelData[channelNumber] = []
            self.ChannelData[channelNumber].append(step)


class ThresholdScan(Scan):
    def __init__(self):
        Scan.__init__(self, "ThresholdScan", True)


class VoltageScan(Scan):
    def __init__(self):
        Scan.__init__(self, "VoltageScan", True)

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
        vrms.SetMaximum(5)
        irms.SetMaximum(5)

        for channelNumber, steps in self.ChannelData.iteritems():
            channels.append(float(channelNumber))
            channelserr.append(0.0)

            # pulling relevant data
            dac, v, i = array('f'), array('f'), array('f')

            for step in steps:
                dac.append(float(step["VsetDAC"]))
                v.append(float(step["V"]))
                i.append(float(step["I"]))
                
                bin = vrms.FindBin(float(step["VsetDAC"]), float(channelNumber))
                vrms.SetBinContent(bin, float(step["Vrms"]))
                irms.SetBinContent(bin, float(step["Irms"]))

            # creating and fitting each graph
            vdacgraph, vdacfit = self._createAndFitGraph(dac, v, int(channelNumber)%8)
            vslopes.append(vdacfit.GetParameter(1))
            vslopeserr.append(vdacfit.GetParError(1))
            vints.append(vdacfit.GetParameter(0))
            vintserr.append(vdacfit.GetParError(0))

            ivgraph, ivfit = self._createAndFitGraph(i, v, int(channelNumber)%8)
            islopes.append(ivfit.GetParameter(1))
            islopeserr.append(ivfit.GetParError(1))

            idacgraph, idacfit = self._createAndFitGraph(dac, i, int(channelNumber)%8)

            fitgraphs.append((vdacgraph, ivgraph, idacgraph))

        if showFits:
            datacanvas = ROOT.TCanvas("datacanvas", "Data and fits")
            datacanvas.Divide(1,3)

            vmultigraph, ivmultigraph, imultigraph = ROOT.TMultiGraph(), ROOT.TMultiGraph(), ROOT.TMultiGraph()
            for graphs in fitgraphs:
                vmultigraph.Add(graphs[0])
                ivmultigraph.Add(graphs[1])
                imultigraph.Add(graphs[2])

            datacanvas.cd(1)
            vmultigraph.Draw("ap")
            vmultigraph.GetXaxis().SetTitle("VsetDAC")
            vmultigraph.GetYaxis().SetTitle("V")
            datacanvas.cd(2)
            ivmultigraph.Draw("ap")
            ivmultigraph.GetXaxis().SetTitle("I")
            ivmultigraph.GetYaxis().SetTitle("V")
            datacanvas.cd(3)
            imultigraph.Draw("ap")
            imultigraph.GetXaxis().SetTitle("VsetDAC")
            imultigraph.GetYaxis().SetTitle("I")

        fitcanvas = ROOT.TCanvas("fitcanvas", "Fit results")
        fitcanvas.Divide(3,1)

        fitcanvas.cd(1)
        vintsgraph = ROOT.TGraphErrors(len(channels), channels, vints, channelserr, vintserr)
        vintsgraph.SetTitle("Intercept [V]")
        vintsgraph.SetMarkerStyle(4)
        vintsgraph.GetXaxis().SetLimits(-1,17)
        vintsHasProblem = self._checkAndDraw(vintsgraph, vints, 0.1)
        hasProblem = hasProblem or vintsHasProblem

        fitcanvas.cd(2)
        vslopesgraph = ROOT.TGraphErrors(len(channels), channels, vslopes, channelserr, vslopeserr)
        vslopesgraph.SetTitle("Slope V vs DAC")
        vslopesgraph.SetMarkerStyle(4)
        vslopesgraph.GetXaxis().SetLimits(-1,17)
        vslopesHasProblem = self._checkAndDraw(vslopesgraph, vslopes, 0.1)
        hasProblem = hasProblem or vslopesHasProblem

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


class BiasVoltageScan(Scan):
    def __init__(self):
        Scan.__init__(self, "BiasVoltageScan", False)

    def visualizeAndCheck(self):
        hasProblem = False

        dac, v, i, dv, di = array('f'), array('f'), array('f'), array('f'), array('f')
        for step in self.Data:
            dac.append(float(step["VsetDAC"]))
            v.append(float(step["V"]))
            i.append(float(step["I"]))
            dv.append(float(step["dV"]))
            di.append(float(step["dI"]))

        vgraph = self._createAndFitGraph(dac, v)
        igraph = self._createAndFitGraph(dac, i)
        dvgraph = ROOT.TGraph(len(dac), dac, dv)
        digraph = ROOT.TGraph(len(dac), dac, di)

        biascanvas = ROOT.TCanvas("biascanvas", "Bias voltage scan results")
        biascanvas.Divide(2,2)

        biascanvas.cd(1)
        vgraph.Draw("ap")
        self._setAxes(vgraph, "VsetDAC", "V[V]")

        biascanvas.cd(2)
        igraph.Draw("ap")
        self._setAxes(igraph, "VsetDAC", "I[A]")

        biascanvas.cd(3)
        dvgraph.Draw("ap")
        self._setAxes(dvgraph, "VsetDAC", "dV[mV]")

        biascanvas.cd(4)
        digraph.Draw("ap")
        self._setAxes(digraph, "VsetDAC", "dI[mA]")

        raw_input("Press enter to continue")

        return hasProblem

    def _createAndFitGraph(self, x, y):
        graph = ROOT.TGraph(len(x), x, y)
        graph.Fit('pol1')
        return graph

    def _setAxes(self, graph, xtitle, ytitle):
        graph.SetMarkerStyle(4)
        graph.SetTitle("")
        graph.GetXaxis().SetTitle(xtitle)
        graph.GetYaxis().SetTitle(ytitle)

class TemperatureScan(Scan):
    def __init__(self):
        Scan.__init__(self, "TemperatureScan", False)


class LatchupTest(Scan):
    def __init__(self):
        Scan.__init__(self, "LatchupTest", False)


class TestInfo(object):
    def __init__(self):
        self.Data = {}

    def parseFilename(self, filename):
        metadata = filename.split("_")

        self.Data["Timestamp"] = metadata[0]
        # strip off "BoardID"
        self.Data["BoardNumber"] = metadata[1][7:]
        # strip off "v"
        self.Data["BoardVersion"] = metadata[2][1:]
        # strip off "PowerUnitID"
        self.Data["PowerUnit"] = metadata[3][11:]
        # strip off "LoadType"
        self.Data["LoadType"] = metadata[4][8:]
        # strip off "Config"
        self.Data["Config"] = metadata[5][6:]
        # strip off ".txt"
        self.Data["Tester"] = metadata[7][:-4]


    def readDB(self, boardNumber, testId=0):
        self.Data = db.getRows("TestInfo", boardNumber, testId)[0]
        self.Id = self.Data["Id"]
