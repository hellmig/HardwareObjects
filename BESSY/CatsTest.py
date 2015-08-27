
from HardwareRepository import BaseHardwareObjects
import logging

# from PyTango import DeviceProxy

class CatsTest(BaseHardwareObjects.Device):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)

    def init(self):
        # devname = self.getProperty("tangoname")
        # self.device = DeviceProxy(devname) 
        self.open_cmd = self.getCommandObject("Open")
        self.close_cmd = self.getCommandObject("Close")

    def openlid1(self):
        #self.device.openlid1()
        import time
        t0=time.time()
        print self.getChannelObject("last_image_saved").getValue()
        print time.time()-t0
        #self.open_cmd()

    def closelid1(self):
        #self.device.closelid1()
        self.close_cmd()

    #def init(self):
        #try:
            #self.topupMode = self.getChannelObject('topup_mode')
        #except KeyError:
            #logging.getLogger().warning('TopupMode: error initializing arguments (missing channel: topup_mode)')
            #self.topupMode = None
#
        #if self.topupMode is not None:
            #self.connect(self.topupMode,'update',self.topupModeChanged)

