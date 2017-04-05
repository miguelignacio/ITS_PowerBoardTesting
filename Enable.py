#!/usr/bin/python

from __future__ import division
import os
import io
import sys
import time
from definitions import WriteToDevice
from definitions import ReadFromDevice
from definitions import ReadRSFromDevice
import math
import datetime

THaddress = (0x31, 0x33, 0x43, 0x51)
ENaddress = (0x20, 0x27)

def enable(board,chMask):
        board = int(board)
        ENadd = int(ENaddress[board])

        enMask = (~chMask & 0xFF)

        WriteToDevice(int(ENaddress[board]), int(enMask)) # Enable the Outputs
        WriteToDevice(int(ENaddress[board]), 0xFF) # Enable the Latch Read Back

        print "Channels Enabled"

        return 0

