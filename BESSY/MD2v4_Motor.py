from HardwareRepository.BaseHardwareObjects import Device
import math
import logging
import time
import gevent
import PyTango

class MD2v4TimeoutError(Exception):
    pass

class MD2v4_Motor(Device):      
    (NOTINITIALIZED, UNUSABLE, READY, MOVESTARTED, MOVING, ONLIMIT) = (0,1,2,3,4,5)
    EXPORTER_TO_MOTOR_STATE = { "Invalid": NOTINITIALIZED,
                                "Fault": UNUSABLE,
                                "Ready": READY,
                                "Moving": MOVING,
                                "Created": NOTINITIALIZED,
                                "Initializing": NOTINITIALIZED,
                                "Unknown": UNUSABLE }

    def __init__(self, name):
        Device.__init__(self, name)

    def init(self): 
        self.motorState = MD2v4_Motor.NOTINITIALIZED
        self.offset = self.getProperty("offset")
        self.position_attr = self.getChannelObject("motor_attr")
        self.position_attr.connectSignal("update", self.motorPositionChanged)
        self.state_attr = self.getChannelObject("device_state")
        # self.state_attr.connectSignal("update", self.globalStateChanged)
        self.motors_state_attr = self.getChannelObject("motor_states")
        self.motors_state_attr.connectSignal("update", self.updateMotorState)
        self._motor_abort = self.getCommandObject("motor_abort")

        # this is ugly : I added it to make the centring procedure happy
        self.specName = self.motor_name

    def connectNotify(self, signal):
        if signal == 'positionChanged':
                self.emit('positionChanged', (self.getPosition(), ))
        elif signal == 'stateChanged':
                self.motorStateChanged(self.getState())
        elif signal == 'limitsChanged':
                self.motorLimitsChanged()  
 
    def updateState(self):
        self.setIsReady(self.motorState > MD2v4_Motor.UNUSABLE)

    def updateMotorState(self, motor_states):
        # print "MD2v4_Motor.updateMotorState", motor_states
        d = dict([x.split("=") for x in motor_states.split()])
        new_motor_state = int(d[self.motor_name])
        if self.motorState == new_motor_state:
          return
        self.motorState = new_motor_state
        self.motorStateChanged(self.motorState)

    def motorStateChanged(self, state):
        logging.getLogger().debug("%s: in motorStateChanged: motor state changed to %s", self.name(), state)
        self.updateState()
        self.emit('stateChanged', (self.motorState, ))

    def getState(self):
        if self.motorState == MD2v4_Motor.NOTINITIALIZED:
          self.updateMotorState(self.motors_state_attr.getValue())
        return self.motorState
    
    def motorLimitsChanged(self):
        self.emit('limitsChanged', (self.getLimits(), ))
                     
    def getLimits(self):
        return (-1E4,1E4)
        try:
          info = self.position_attr.getInfo()
          low_lim,hi_lim = map(float, (float(info.min_value)+self.offset, float(info.max_value)+self.offset))
          if low_lim==float(1E999) or hi_lim==float(1E999):
            raise ValueError
          return low_lim, hi_lim
        except:
          return (-1E4, 1E4)
 
    def motorPositionChanged(self, absolutePosition, private={}):
        if math.fabs(absolutePosition - private.get("old_pos", 1E12))<=1E-3:
          return 
        private["old_pos"]=absolutePosition 

        self.emit('positionChanged', (absolutePosition, ))

    def getPosition(self):
        return self.position_attr.getValue()

    def getDialPosition(self):
        return self.getPosition()

    def move(self, absolutePosition):
        self.position_attr.setValue(absolutePosition) #absolutePosition-self.offset)
        self.motorStateChanged(MD2v4_Motor.MOVING)

    def moveRelative(self, relativePosition):
        self.move(self.getPosition() + relativePosition)

    def syncMoveRelative(self, relative_position, timeout=None):
        return self.syncMove(self.getPosition() + relative_position)

    def waitEndOfMove(self, timeout=None):
        with gevent.Timeout(timeout):
           time.sleep(0.1)
           while (self.state_attr.getValue() == PyTango.DevState.MOVING) or (self.motorState == MD2v4_Motor.MOVING):
              time.sleep(0.1) 

    def syncMove(self, position, timeout=None):
        self.move(position)
        try:
          self.waitEndOfMove(timeout)
        except:
          raise MD2v4TimeoutError

    def motorIsMoving(self):
        return self.isReady() and self.motorState == MD2v4_Motor.MOVING 
 
    def getMotorMnemonic(self):
        return self.motor_name

    def stop(self):
        self._motor_abort()
