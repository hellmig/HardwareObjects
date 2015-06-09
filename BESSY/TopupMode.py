from HardwareRepository import BaseHardwareObjects
import logging

class TopupMode(BaseHardwareObjects.Device):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)

    def init(self):
        try:
            self.topupMode = self.getChannelObject('topup_mode')
        except KeyError:
            logging.getLogger().warning('TopupMode: error initializing arguments (missing channel: topup_mode)')
            self.topupMode = None

        if self.topupMode is not None:
            self.connect(self.topupMode,'update',self.topupModeChanged)

    def topupModeChanged(self, value):
        self.emit('valueChanged', (value))
