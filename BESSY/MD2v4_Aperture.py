import MD2v4_Motor
import logging
import math

class MD2v4_Aperture(MD2v4_Motor.MD2v4_Motor):      
    def __init__(self, name):
        MD2v4_Motor.MD2v4_Motor.__init__(self, name)

    def init(self):
        MD2v4_Motor.MD2v4_Motor.init(self)

        self.predefinedPositions = {}
        self.tangoname = self.getProperty("tangoname")
        self.labels = self.getChannelObject("diameter_attr")
        self.filters = self.labels.getValue()
        self.nb = len(self.filters)
        j = 0
        while j < self.nb :
          for i in self.filters: #.split() :
            if int(i) >= 300:
              i = "Outbeam"
            self.predefinedPositions[i] = j
            j = j+1
        self.sortPredefinedPositionsList()
        
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
        return (1,self.nb)

    def getPredefinedPositionsList(self):
        return self.predefinedPositionsNamesList

    def motorPositionChanged(self, absolutePosition, private={}):
        MD2v4_Motor.MD2v4_Motor.motorPositionChanged.im_func(self, absolutePosition, private)

        positionName = self.getCurrentPositionName(absolutePosition)
        self.emit('predefinedPositionChanged', (positionName, positionName and absolutePosition or None, ))

    def getCurrentPositionName(self, pos=None):
        if self.getPosition() is not None:
          pos = pos or self.getPosition()
        else :
          pos = pos
        for positionName in self.predefinedPositions:
          if math.fabs(self.predefinedPositions[positionName] - pos) <= 1E-3:
            return positionName
        return ''

    def moveToPosition(self, positionName):
        logging.getLogger().debug("%s: trying to move %s to %s:%f", self.name(), self.motor_name, positionName,self.predefinedPositions[positionName])
        try:
            self.move(self.predefinedPositions[positionName])
        except:
            logging.getLogger("HWR").exception('Cannot move motor %s: invalid position name.', str(self.userName()))

    def setNewPredefinedPosition(self, positionName, positionOffset):
        raise NotImplementedError

    def getApertureCoef(self):
        diameter_name = self.getCurrentPositionName()
        for diameter in self["diameter"]:
            if str(diameter.getProperty("name")) == str(diameter_name):
                aperture_coef = diameter.getProperty("aperture_coef")
                return float(aperture_coef)
        return 1
