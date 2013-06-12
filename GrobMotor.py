from HardwareRepository.BaseHardwareObjects import Device
import math
import logging
import time
import gevent
import types

class GrobMotor(Device):      
    (NOTINITIALIZED, UNUSABLE, READY, MOVESTARTED, MOVING, ONLIMIT) = (0,1,2,3,4,5)

    def __init__(self, name):
        Device.__init__(self, name)

    def init(self): 
        self.motorState = GrobMotor.NOTINITIALIZED
        self.username = self.motor_name
        self.grob = self.getObjectByRole("grob")

        # this is ugly : I added it to make the centring procedure happy
        self.specName = self.motor_name

        self.motor = getattr(self.grob.controller, self.motor_name)
        self.connect(self.motor, "position", self.positionChanged)
        self.connect(self.motor, "state", self.updateState)

    def connectNotify(self, signal):
        if signal == 'positionChanged':
                self.emit('positionChanged', (self.getPosition(), ))
        elif signal == 'stateChanged':
                self.updateState()
        elif signal == 'limitsChanged':
                self.motorLimitsChanged()  
 
    def updateState(self, state=None):
        if state is None:
            state = self.motor.state()
            if isinstance(self.motor, self.grob.SampleTableMotor):
                if self.motor.is_unusable():
                    state = "UNUSABLE"
                elif self.motor.is_moving(state):
                    state = "MOVING"
                elif self.motor.is_on_limit(state):
                    state = "ONLIMIT"
                else:
                    state = "READY"
        # convert from grob state to Hardware Object motor state
        if state == "MOVING":
            state = GrobMotor.MOVING
        elif state == "READY" or state.startswith("WAIT_GET"):
            state = GrobMotor.READY
        elif state == "ONLIMIT":
            state = GrobMotor.ONLIMIT
        else:
            state = GrobMotor.UNUSABLE

        self.setIsReady(state > GrobMotor.UNUSABLE)

        if self.motorState != state:
            self.motorState = state 
            self.emit('stateChanged', (self.motorState, ))

    def getState(self):
        self.updateState()
        return self.motorState
    
    def motorLimitsChanged(self):
        self.emit('limitsChanged', (self.getLimits(), ))
                     
    def getLimits(self):
        return self.motor.get_limits()

    def positionChanged(self, absolutePosition, private={}):
        if math.fabs(absolutePosition - private.get("old_pos", 1E12))<=1E-3:
          return 
        private["old_pos"]=absolutePosition 

        self.emit('positionChanged', (absolutePosition, ))

    def getPosition(self):
        return self.motor.read_dial()

    def getDialPosition(self):
        return self.getPosition()

    def move(self, position):
        if isinstance(self.motor, self.grob.SampleMotor):
          # position has to be relative
          self.motor.move_relative(position - self.getPosition())
        else:
          self.motor.start_one(position) 

    def moveRelative(self, relativePosition):
        self.move(self.getPosition() + relativePosition)

    def syncMoveRelative(self, relative_position, timeout=None):
        return self.syncMove(self.getPosition() + relative_position)

    def waitEndOfMove(self, timeout=None):
        with gevent.Timeout(timeout):
           self.motor.wait_for_move()

    def syncMove(self, position, timeout=None):
        self.move(position)
        try:
          self.waitEndOfMove(timeout)
        except:
          raise MD2TimeoutError

    def motorIsMoving(self):
        return self.isReady() and self.motor.is_moving()
 
    def getMotorMnemonic(self):
        return self.motor_name

    def stop(self):
        pass
