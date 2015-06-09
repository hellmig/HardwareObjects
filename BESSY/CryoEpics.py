import logging

from HardwareRepository.BaseHardwareObjects import Device

CRYO_STATUS = ["OFF", "SATURATED", "READY", "WARNING", "FROZEN" , "UNKNOWN"]

class CryoEpics(Device):
    def __init__(self, name):
        Device.__init__(self, name)
        self.temp = None
	self.n2level = None
        
    def init(self):
        # set up connection to the cryostream EPICS PV
        try:
            self.cryotemp = self.getChannelObject('cryo_temp')
        except KeyError:
            logging.getLogger().warning('CryoEpics: error initializing arguments (missing channel: cryo_temp)')
            self.cryotemp = None
        if self.cryotemp is not None:
            self.connect(self.cryotemp, 'update', self.valueChanged)
            self.setIsReady(True)
        
        # call ringCurrentChanged manually once in order to initialize view
        self.valueChanged()

    def valueChanged(self, value = None):
        temp_error = None
        if value is not None:
            temp = value
        else:
            temp = 0
            if self.cryotemp is not None:
                temp = self.cryotemp.getValue()

        if temp != self.temp:
            self.temp = temp
            self.emit("temperatureChanged", (temp, temp_error, ))

    def setN2Level(self, newLevel):
        pass

    def getTemperature(self):
        return self.temp
