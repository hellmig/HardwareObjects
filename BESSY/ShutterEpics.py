#$Id: ShutterEpics.py,v 0.1 2011/08/16 hellmig $
import logging

from HardwareRepository.BaseHardwareObjects import Device

class ShutterEpics(Device):
    shutterState = {
        0: 'unknown',
        1: 'closed',
        2: 'opened',
        3: 'unknown'
        }

  
    def __init__(self, name):
        Device.__init__(self, name)

        self.shutterStateValue = 0
        self.safshut = None


    def init(self):
        # set up connection to the secondary beam shutter EPICS PV
        try:
            self.safshut = self.getChannelObject('safshut_status')
        except KeyError:
            logging.getLogger().warning('ShutterEpics: error initializing arguments (missing channel: safshut_status)')
            self.safshut = None
        if self.safshut is not None:
            self.connect(self.safshut, 'update', self.safshutChanged)
            self.setIsReady(True)
        
        # call ringCurrentChanged manually once in order to initialize view
        self.safshutChanged()

    def connectNotify(self, signal):
        if signal == 'shutterStateChanged':
                pass
                #print "connectNotify shutterStateChanged"
                #self.safshutChanged()
                # self.emit('shutterStateChanged', (self.safshutChanged(), ))

    def getShutterState(self):
        return ShutterEpics.shutterState[self.shutterStateValue] 
        

    def isShutterOk(self):
        return not self.getShutterState() in ('unknown', 'moving', 'fault', 'disabled', 'error')


    def openShutter(self):
        logging.getLogger("HWR").warning("%s: due to radiation-safety regulations shutter must be operated manually. Current status: >%s<.", self.name(), self.getShutterState())
            

    def closeShutter(self):
        logging.getLogger("HWR").warning("%s: due to radiation-safety regulations shutter must be operated manually. Current status: >%s<.", self.name(), self.getShutterState())


    def safshutChanged(self, value = None):
        #
        # emit signal
        #
        if value is None:
            value = 0
            if self.safshut is not None:
                value = self.safshut.getValue()

        if value is not None:
            self.shutterStateValue = value
            self.emit('shutterStateChanged', (ShutterEpics.shutterState[self.shutterStateValue], ShutterEpics.shutterState[self.shutterStateValue], ))

