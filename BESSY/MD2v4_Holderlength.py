import MD2v4_Motor
import math
import logging
import time

class MD2v4_Holderlength(MD2v4_Motor.MD2v4_Motor):     
    def __init__(self, *args):
        MD2v4_Motor.MD2v4_Motor.__init__(self, *args)
 
    def init(self): 
        MD2v4_Motor.MD2v4_Motor.init(self)

        self.offset_chan = self.getChannelObject("length_attr")
        #self.offset_chan.connectSignal("update", self.offsetChanged)
        #self.offset = self.offset_chan.getValue()

    #def offsetChanged(self, new_offset):
    #    self.offset = new_offset

    def motorPositionChanged(self, absolutePosition, private={}):
        if math.fabs(absolutePosition - private.get("old_pos", 1E12))<=1E-3:
          return 
        private["old_pos"]=absolutePosition 

        self.emit('positionChanged', (self.offset_chan.getValue() - absolutePosition, ))

    def getPosition(self):
        return self.offset_chan.getValue() - self.position_attr.getValue()

    def move(self, absolutePosition):
        self.position_attr.setValue(self.offset_chan.getValue() - absolutePosition) #absolutePosition-self.offset)
