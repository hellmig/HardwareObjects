from MicrodiffMotor import MicrodiffMotor
import logging
import math

class MicrodiffSamplePseudo(MicrodiffMotor):      
    def __init__(self, name):
        MicrodiffMotor.__init__(self, name)
        
        self.motor_name = name
        self.sampx = None
        self.sampy = None
        self.phi = None
        self.direction = None
        self.motorState = MicrodiffMotor.NOTINITIALIZED 

    def init(self): 
        self.direction = self.getProperty("direction")
        self.sampx = self.getObjectByRole("sampx")
        self.sampy = self.getObjectByRole("sampy")
        self.phi = self.getObjectByRole("phi")
        self.connect(self.sampx, "positionChanged", self.real_motor_moved)
        self.connect(self.sampx, "stateChanged", self.real_motor_changed)
        self.connect(self.sampy, "positionChanged", self.real_motor_moved)
        self.connect(self.sampy, "stateChanged", self.real_motor_changed)
        self.connect(self.phi, "positionChanged", self.real_motor_moved)
        self.connect(self.phi, "stateChanged", self.real_motor_changed)

    def real_motor_moved(self, _):
        self.motorPositionChanged(self.getPosition())
          
    def updateMotorState(self):
        states = [m.getState() for m in (self.sampx, self.sampy, self.phi)]
        error_states = [state in (MicrodiffMotor.UNUSABLE, MicrodiffMotor.NOTINITIALIZED, MicrodiffMotor.ONLIMIT) for state in states]
        moving_state = [state in (MicrodiffMotor.MOVING, MicrodiffMotor.MOVESTARTED) for state in states]
 
        if any(error_states):
          self.motorState = MicrodiffMotor.UNUSABLE
        elif any(moving_state):
          self.motorState = MicrodiffMotor.MOVING
        else:
          self.motorState = MicrodiffMotor.READY
 
        self.motorStateChanged(self.motorState)
    
    def motorStateChanged(self, state):
        logging.getLogger().debug("%s: in motorStateChanged: motor state changed to %s", self.name(), state)
        self.emit('stateChanged', (self.motorState, ))

    def getPosition(self):
        sampx = self.sampx.getPosition()
        sampy = self.sampy.getPosition()
        phi = math.radians(self.phi.getPosition())
        if self.direction == "horizontal":
          new_pos = sampx*math.cos(phi)+sampy*math.sin(phi)
        else:
          new_pos = sampx*math.sin(-phi)+sampy*math.cos(-phi)
        return new_pos

    def getState(self):
        if self.motorState == MicrodiffMotor.NOTINITIALIZED:
          self.updateMotorState()
        return self.motorState
   
    def real_motor_changed(self, _):
        self.updateMotorState()
 
    def motorPositionChanged(self, absolutePosition):
        self.emit('positionChanged', (absolutePosition, ))

    def move(self, absolutePosition):
        sampx = self.sampx.getPosition()
        sampy = self.sampy.getPosition()
        phi = math.radians(self.phi.getPosition())
        if self.direction == 'horizontal':
          ver = sampx*math.sin(-phi)+sampy*math.cos(-phi)
          self.sampx.move(absolutePosition*math.cos(-phi)+ver*math.sin(-phi))
          self.sampy.move(-absolutePosition*math.sin(-phi)+ver*math.cos(-phi))
        else:
          hor = sampx*math.cos(phi)+sampy*math.sin(phi)
          self.sampx.move(absolutePosition*math.sin(-phi)+hor*math.cos(-phi))
          self.sampy.move(absolutePosition*math.cos(-phi)-hor*math.sin(-phi))
 
    def _motor_abort(self):
        for m in (self.phi, self.sampx, self.sampy):
            m.stop()



