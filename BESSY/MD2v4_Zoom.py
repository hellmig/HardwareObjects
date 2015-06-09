import MD2v4_Motor
import logging
import math
import time

class MD2v4_Zoom(MD2v4_Motor.MD2v4_Motor):      
    def __init__(self, name):
        MD2v4_Motor.MD2v4_Motor.__init__(self, name)

    def init(self):
        MD2v4_Motor.MD2v4_Motor.init(self)

        self.predefined_position_attr = self.getChannelObject("predefined_position_attr")
        #if self.predefined_position_attr is not None:
        #    self.predefined_position_attr.connectSignal("update", self.zoomPositionChanged)
        self.predefinedPositions = { "Zoom 1": 1, "Zoom 2": 2, "Zoom 3": 3, "Zoom 4": 4, "Zoom 5": 5, "Zoom 6": 6, "Zoom 7": 7, "Zoom 8": 8, "Zoom 9": 9, "Zoom 10":10 }
        self.sortPredefinedPositionsList()

    #def zoomPositionChanged(self, value):
    #    print "MD2v4_Zoom.zoomPositionChanged"
    #    self.emit("minidiffReady", ())

    def sortPredefinedPositionsList(self):
        self.predefinedPositionsNamesList = self.predefinedPositions.keys()
        self.predefinedPositionsNamesList.sort(lambda x, y: int(round(self.predefinedPositions[x] - self.predefinedPositions[y])))

    def connectNotify(self, signal):
        if signal == 'predefinedPositionChanged':
            positionName = self.getCurrentPositionName()

            try:
                pos = self.predefinedPositions[positionName]
            except KeyError:
                self.emit(signal, ('', None))
            else:
                self.emit(signal, (positionName, pos))
        else:
            return MD2v4_Motor.MD2v4_Motor.connectNotify.im_func(self, signal)

    def getLimits(self):
        return (1,10)

    def getPredefinedPositionsList(self):
        return self.predefinedPositionsNamesList

    def motorPositionChanged(self, absolutePosition, private={}):
        MD2v4_Motor.MD2v4_Motor.motorPositionChanged.im_func(self, absolutePosition, private)

        positionName = self.getCurrentPositionName(absolutePosition)
        self.emit('predefinedPositionChanged', (positionName, positionName and absolutePosition or None, ))

    def getCurrentPositionName(self, pos=None):
        pos = self.predefined_position_attr.getValue()

        for positionName in self.predefinedPositions:
          if math.fabs(self.predefinedPositions[positionName] - pos) <= 1E-3:
            return positionName
        return ''

    def moveToPosition(self, positionName):
        logging.getLogger().debug("%s: trying to move %s to %s:%f", self.name(), self.motor_name, positionName,self.predefinedPositions[positionName])
        try:
            self.predefined_position_attr.setValue(self.predefinedPositions[positionName])
            # time.sleep(0.5)
        except:
            logging.getLogger("HWR").exception('Cannot move motor %s: invalid position name.', str(self.userName()))

    def setNewPredefinedPosition(self, positionName, positionOffset):
        raise NotImplementedError

    def motorStateChanged(self, state):
        logging.getLogger().debug("%s: in motorStateChanged: motor state changed to %s", self.name(), state)
        MD2v4_Motor.MD2v4_Motor.motorStateChanged(self, state)

