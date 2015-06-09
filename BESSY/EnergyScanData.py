from qt import QObject
from HardwareRepository.BaseHardwareObjects import Procedure
from HardwareRepository import HardwareRepository

try:
  from SpecClient_gevent import SpecScan
except ImportError:
  from SpecClient import SpecScan

import logging

class QSpecScan(object):
    def __init__(self):
        self.x = []
        self.y = []


"""
EnergyScanData
    Type: class
"""
class EnergyScanData(Procedure):
    def init(self):
        print "***** EnergyScanData HO *****"
        self.scanObject = None
        try:
            self.scanData=self.getChannelObject('energy_scan_data')
        except KeyError:
            self.scanData=None
            logging.getLogger("HWR").warning('EnergyScanData: energy scan data not configured')
        #else:
        #    self.connect(self.scanData,'update',self.scanDataChanged)

    def scanDataChanged(self):
        print self.scanData.getValue()

    def isConnected(self):
        return (self.scanData is not None and scanObject.isConnected())

    def isDisconnected(self):
        return not (self.configOk and self.scanObject.isConnected())

    def getScanData(self):
        return self.scanObject

    def readDataFromFile(self, filename):
        pass

    def writeDataToFile(self, filename):
        pass
