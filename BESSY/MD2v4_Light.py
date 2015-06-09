from HardwareRepository.BaseHardwareObjects import Device
import math
import logging
import time

class MD2v4_Light(Device):      
    (NOTINITIALIZED, UNUSABLE, READY, MOVESTARTED, MOVING, ONLIMIT) = (0,1,2,3,4,5)

    def __init__(self, name):
        Device.__init__(self, name)

    def init(self): 
        self.motorState = MD2v4_Light.READY
        self.global_state = "STANDBY"
        self.position_attr = self.getChannelObject("position_attr")
        self.position_attr.connectSignal("update", self.motorPositionChanged)
        self.setIsReady(True)
        # this is ugly : I added it to make the centring procedure happy
        self.specName = self.motor_name

    def connectNotify(self, signal):
        if self.position_attr.isConnected():
            if signal == 'positionChanged':
                self.emit('positionChanged', (self.getPosition(), ))
            elif signal == 'limitsChanged':
                self.motorLimitsChanged()  
 
    def updateState(self):
        self.setIsReady(True) #self.global_state in ("STANDBY","ALARM") and self.motorState > MD2v4_Light.UNUSABLE)
 
    def getState(self):
        return self.motorState
    
    def motorLimitsChanged(self):
        self.emit('limitsChanged', (self.getLimits(), ))
                     
    def getLimits(self):
        return (0, 100)
 
    def motorPositionChanged(self, absolutePosition, private={}):
        self.emit('positionChanged', (absolutePosition, ))
        self.updateState()
        self.emit('stateChanged', (self.motorState, ))

    def getPosition(self):
        return self.position_attr.getValue()

    def move(self, absolutePosition):
        self.position_attr.setValue(absolutePosition)

    def moveRelative(self, relativePosition):
        self.move(self.getPosition() + relativePosition)

    def getMotorMnemonic(self):
        return self.motor_name

    def stop(self):
        pass #self._motor_abort()
    
