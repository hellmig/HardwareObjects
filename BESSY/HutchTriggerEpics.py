import logging
from HardwareRepository.BaseHardwareObjects import Device

# do we really need this???: import qt

class HutchTriggerEpics(Device):
    def __init__(self, name):
        Device.__init__(self, name)


    def init(self):
        self.initialized = False
        self.__oldValue = None
        self.cmdHutchTrigger = None

        # set up connection to the secondary beam shutter EPICS PV
        try:
            self.doorStatus = self.getChannelObject('door_status')
        except KeyError:
            logging.getLogger().warning('HutchTriggerEpics: error initializing HutchTriggerEpics arguments (missing channel: door_status)')
            self.doorStatus = None
        if self.doorStatus is not None:
            self.connect(self.doorStatus, 'update', self.doorStatusChanged)
        
        # hutchtrigger spec macro to carry out movements
        self.cmdHutchTrigger = self.getCommandObject('macro')
        self.cmdHutchTrigger.connectSignal('connected', self.connected)
        self.cmdHutchTrigger.connectSignal('disconnected', self.disconnected)
        self.cmdHutchTrigger.connectSignal('commandBeginWaitReply', self.macroStarted)
        self.cmdHutchTrigger.connectSignal('commandReplyArrived', self.macroDone)
        self.cmdHutchTrigger.connectSignal('commandFailed', self.macroFailed)
        #self.cmdHutchTrigger.connectSignal('commandAborted', self.macroDone)
        try:
            chanStatus = self.getChannelObject('status')
        except KeyError:
            logging.getLogger().warning('%s: cannot report status', self.name())
        else:
            chanStatus.connectSignal('update', self.statusChanged)
        try:
            chanMsg = self.getChannelObject('msg')
        except KeyError:
            logging.getLogger().warning('%s: cannot show messages', self.name())
        else:
            chanMsg.connectSignal('update', self.msgChanged)
        
        if self.cmdHutchTrigger.isConnected():
            self.connected()

        # call doorStatusChanged manually once in order to initialize view
        self.doorStatusChanged()


    def isConnected(self):
        return self.cmdHutchTrigger.isConnected()

        
    def connected(self):
        self.setIsReady(True)
        self.emit('connected')
        
        
    def disconnected(self):
        self.emit('disconnected')
        self.setIsReady(False)


    def macroStarted(self):
        self.emit('macroStarted')


    def macroDone(self):
        self.emit('macroDone')


    def macroFailed(self):
        self.emit('macroFailed')


    def abort(self):
        self.cmdHutchTrigger.abort()
        
        
    def msgChanged(self, channelValue):
        self.emit('msgChanged', (channelValue, ))


    def statusChanged(self, channelValue):
        self.emit('statusChanged', (channelValue, ))


    def hutchIsOpened(self):
        status=self.doorStatus.getValue()

        logging.info("HutchTriggerEpics: hutchIsOpen returns %s" % status)
        if status=="locked":
             return False
        else:
             return True

    def doorStatusChanged(self, value = None):
        # print "HutchTriggerEpics.doorStatusChanged: new status value = %s" % value

        if value == None:
            value = 'unknown'
            if self.doorStatus is not None:
                value = self.doorStatus.getValue()

        if value == self.__oldValue:
            return
        else:
            self.__oldValue = value
        
        if self.initialized:
            if value == 'locked':
                # door of experimental hutch locked and interlock set
                self.emit('hutchTrigger', (0, ))
            elif value == 'unlocked':
                # door of experimental hutch unlocked and interlock cleared
                self.emit('hutchTrigger', (1, ))
            else:
                # shutter status unknown or error
                pass

	self.initialized = True

