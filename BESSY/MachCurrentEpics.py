from HardwareRepository import BaseHardwareObjects
import logging

class MachCurrentEpics(BaseHardwareObjects.Device):
    def __init__(self, name):
        BaseHardwareObjects.Device.__init__(self, name)

        self.machValue = None
        self.fillModeStr = None
        self.lifeTimeValue = None

    def init(self):
        try:
            self.ringCurrent = self.getChannelObject('ring_current')
        except KeyError:
            logging.getLogger().warning('MachCurrentEpics: error initializing arguments (missing channel: ring_current)')
            self.ringCurrent = None
        try:
            self.fillMode = self.getChannelObject('fill_mode')
        except KeyError:
            logging.getLogger().warning('MachCurrentEpics: error initializing arguments (missing channel: fill_mode)')
            self.fillMode = None
        #try:
        #    self.lifeTime = self.getChannelObject('life_time')
        #except KeyError:
        #    logging.getLogger().warning('MachCurrentEpics: error initializing arguments (missing channel: life_time)')
        #    self.lifeTime = None

        if self.ringCurrent is not None:
            self.connect(self.ringCurrent,'update',self.ringCurrentChanged)

        if self.fillMode is not None:
            self.connect(self.fillMode, 'update', self.fillModeChanged)

    def ringCurrentChanged(self, value):

        self.machValue = value

        # do not get current value for the ring current because it is transferred in the parameter >value<
        #if self.fillMode is not None:
        #    fillModeStr = self.fillMode.getValue()
        #else:
        #    fillModeStr = ''
        #if self.lifeTime is not None:
        #    lifeTimeHours = self.lifeTime.getValue()
        #else:
        #    lifeTimeHours = 0
        ## convert the life time in hours into seconds
        #try:
        #    lifeTimeSeconds = int(round(lifeTimeHours * 3600))
        #except ValueError:
        #    lifeTimeSeconds = 0
        #print self.fillMode
        self.emit('valueChanged', (self.machValue, None, self.fillModeStr, None))
 
    def fillModeChanged(self, value):
        self.fillModeStr = value
        self.emit('valueChanged', (self.machValue, None, self.fillModeStr, None))

    def getCurrent(self):
        #return self.getChannelObject('ring_current').getValue()
        return self.machValue

    def getMessage(self):
        pass

    def getFillMode(self):
        #return self.getChannelObject('fill_mode').getValue()
        return self.fillModeStr
