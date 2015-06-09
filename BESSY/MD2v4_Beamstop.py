from HardwareRepository.BaseHardwareObjects import Equipment
import logging


class MD2v4_Beamstop(Equipment):
    def init(self):
        self.beamstopPosition = self.getChannelObject("beamstop_attr")
        self.beamstopPosition.connectSignal("update", self.checkPosition)
        self.beamstopSetInPosition = self.getCommandObject("beamstop_cmd")

        self.motors = self["motors"]
        self.roles = self.motors.getRoles()
        self.amplitude = 0 #just to make the beamstop brick happy
        self.positions = { "in": 1, "out": 2 }
        self.md2_to_mxcube = { "1": "in", "2": "out" }  
 
        #self.connect("equipmentReady", self.equipmentReady)
        #self.connect("equipmentNotReady", self.equipmentNotReady)
 
  
    def moveToPosition(self, name):
        if name == "in":
            self.beamstopPosition.setValue(1)
        elif name == "out":
            self.beamstopPosition.setValue(2)

  
    def connectNotify(self, signal):
        self.checkPosition()
   
    """ 
    def equipmentReady(self, *args):
        self.checkPosition()

    def equipmentNotReady(self, *args):
        self.checkPosition()
    """

    def isReady(self):
        return True
 
    def getState(self):
        return "READY"

    def getPosition(self):
        return self.checkPosition(noEmit=True)

    def checkPosition(self, pos=None, noEmit=False):
        if pos is None:
            pos = self.beamstopPosition.getValue()
           
        pos = self.md2_to_mxcube.get(str(pos))

        if not noEmit:
          if pos:
            self.emit("positionReached", pos)
          else:
            self.emit("noPosition", ())
        return pos

            
    def setNewPositions(self, name, newPositions):
        if name == "in":
            self.beamstopSetInPosition()
            
        
    def getRoles(self):
        return self.roles
        
