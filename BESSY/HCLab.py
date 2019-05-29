from HardwareRepository.BaseHardwareObjects import Device


"""
Example xml file:
<device class="MicrodiffMotor">
  <username>phiy</username>
  <exporter_address>wid30bmd2s:9001</exporter_address>
  <motor_name>AlignmentY</motor_name>
  <GUIstep>1.0</GUIstep>
  <unit>-1e-3</unit>
  <resolution>1e-2</resolution>
</device>
"""

class HCLab(Device):
    (NOTINITIALIZED, UNUSABLE, READY, STARTED, USING) = (0, 1, 2, 3, 4)
    EXPORTER_TO_HCLAB_STATE = {
        "Running": READY,
        "Alarm": UNUSABLE,    
        "Heating": READY,
    }

    def __init__(self, name):
        Device.__init__(self, name)
    

    def init(self):
        self.humidity=None
        self.state=None

        self.user_name = self.getProperty("username")
        self.humidity_resolution = float(self.getProperty("resolution"))

        self.state_attr = self.getChannelObject("State")
        self.state_attr.connectSignal("update", self.humidityStateChanged)

        #from qt4_debug import bkpoint; bkpoint()
        self.humidity_attr = self.getChannelObject("Humidity")
        self.humidity_attr.connectSignal("update", self.humidityChanged)

    def isReady(self):
        return True

    def humidityChanged(self, absolute_humidity):
        #print "humidity changed"
        if None not in (absolute_humidity, self.humidity):
            if abs(float(absolute_humidity) - float(self.humidity)) <= self.humidity_resolution:
                return
        self.humidity = absolute_humidity
        self.emit("humidityChanged", (self.humidity,))

    def humidityStateChanged(self, state):
        #print "humidity state changed"
        if state is None:
                return
        self.state = state
        self.emit("humidityStateChanged", (self.state,))

    def get_humidityState(self):
        return self.state
    
    def get_humidityValue(self):
        return self.humidity

    def get_setPoint(self):
        return self.setPoint

    def set_point(self,setPoint):
        self.humidity_attr.setValue(setPoint)
        
    def connected(self):
        self.setIsReady(True)
        
    def disconnected(self):
        self.setIsReady(False)
        
    #def setPoint(value):
        
        
    def update_values(self):
        print "update values"
        self.humidity = self.humidity_attr.getValue()
        self.emit("humidityChanged", (self.humidity,))
        self.state = self.state_attr.getValue()
        self.emit("humidityStateChanged", (self.state,))
   




 












  
