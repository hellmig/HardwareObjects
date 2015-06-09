from HardwareRepository import BaseHardwareObjects
import logging

class MachCurrentEpicsSimple(BaseHardwareObjects.Device):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)

    def init(self):
        try:
            self.ringCurrent = self.getChannelObject('ring_current')
        except KeyError:
            logging.getLogger().warning('MachCurrentEpicsSimple: error initializing arguments (missing channel: ring_current)')
            self.ringCurrent = None

        if self.ringCurrent is not None:
            self.connect(self.ringCurrent,'update',self.ringCurrentChanged)

    def ringCurrentChanged(self, value):
        self.emit('valueChanged', (value))

    def getCurrent(self):
        return self.getChannelObject('ring_current').getValue()

    def getMessage(self):
        return "n/a"
