import logging

from HardwareRepository.BaseHardwareObjects import Device

class MD2v4_FastShutter(Device):
    shutterState = {
        0: 'closed',
        1: 'opened',
        }
  
    def __init__(self, name):
        Device.__init__(self, name)

        self.shutterStateValue = 0

        self.fastshut = None
        self.open_cmd = None
        self.close_cmd = None

    def init(self):
        # set up connection to the MD2 fast shutter
        try:
            self.fastshut = self.getChannelObject('dev_state')
        except KeyError:
            logging.getLogger().warning('MD2v4_FastShutter: error initializing arguments (missing channel: dev_state)')
            self.fastshut = None
        if self.fastshut is not None:
            self.connect(self.fastshut, 'update', self.shutterStatusChanged)
            self.setIsReady(True)

        try:
            self.open_cmd = self.getCommandObject("open_shutter_cmd")
        except KeyError:
            logging.getLogger().warning('MD2v4_FastShutter: error initializing arguments (missing command: open_shutter_command)')

        try:
            self.close_cmd = self.getCommandObject("close_shutter_cmd")
        except KeyError:
            logging.getLogger().warning('MD2v4_FastShutter: error initializing arguments (missing command: close_shutter_command)')
        
        # call ringCurrentChanged manually once in order to initialize view
        self.shutterStatusChanged()

    def getShutterState(self):
        return MD2v4_FastShutter.shutterState[self.shutterStateValue] 

    def isShutterOk(self):
        return not self.getShutterState() in ('unknown', 'moving', 'fault', 'disabled', 'error')

    def openShutter(self):
        self.open_cmd()

    def closeShutter(self):
        self.close_cmd()

    def shutterStatusChanged(self, value = None):
        if value == None:
            value = 0
            if self.fastshut is not None:
                value = self.fastshut.getValue()

        if value is not None:
            self.shutterStateValue = value
            self.emit('shutterStateChanged', (MD2v4_FastShutter.shutterState[self.shutterStateValue], ))

