import logging
import os
import stat
from HardwareRepository.BaseHardwareObjects import Equipment 
from PyTango import DevState

#import qt
import math
import gevent
from HardwareRepository.TaskUtils import *

class EscFilters(Equipment):

    filterNames = ["Filter1Bank1", "Filter2Bank1", "Filter3Bank1", "Filter4Bank1", "Filter1Bank2", "Filter2Bank2", "Filter3Bank2", "Filter4Bank2"]


    def __init__(self, name):
        Equipment.__init__(self, name)

        task500ms=self.__timer_500ms_task(wait=False)
        task500ms.link(self._onTimer500msExit)
        

    def init(self):
        self.getXiaFilters = self.addCommand({'type': 'tango', 'name':'getXiaFilters' }, "GetXIAFilters")
        self.putXiaFilters = self.addCommand({'type': 'tango', 'name':'putXiaFilters' }, "PutXIAFilters")
        self.energyMotor = self.getDeviceByRole('energy')

        #if (self.getXiaFilters.isConnected()) and (self.energyMotor is not None):
        #  self.deviceReady()
        #else:
        #  self.deviceNotReady()
        #  return

        self.labels  = []
        self.bits    = []
        self.attno   = 0
        
        self.attState = None
        self.attFactor = None

        self.getAtteConfig()

        # call function once to initialize values attState and attFactor
        self.timeout()

        # set up timer to poll filter state in 1s time intervals
        #self.timer = qt.QTimer()
        #qt.QObject.connect(self.timer, qt.SIGNAL("timeout()"), self.timeout)
        #self.timer.start(1000)

        self.equipmentReady()

        self.connect("equipmentReady", self.equipmentReady)
        self.connect("equipmentNotReady", self.equipmentNotReady)


    def _onTimer500msExit(self, task):
        logging.warning("Exiting ESC filters timer task")
        
        
    @task
    def __timer_500ms_task(self, *args):
        while(True):
            gevent.sleep(0.5)
            self._onTimer500ms()
             

    def _onTimer500ms(self):
        self.timeout()


    def getAtteConfig(self):
        self.attno = len( self['atte'] )

        for att_i in range( self.attno ):
           obj = self['atte'][att_i]
           self.labels.append( obj.label )
           self.bits.append( obj.bits )


    def equipmentReady(self):
        self.emit("deviceReady")


    def equipmentNotReady(self):
        self.emit("deviceNotReady")


    def timeout(self):
        value = self.getXiaFilters(EscFilters.filterNames)
        sum = 0
        for index, item in enumerate(value):
           sum = sum + ((1 << index) * int(item == 1))
        self.attState = sum
        # print "EscFilters.timeout: attState = ", self.attState, type(self.attState)
        # calculate the attenuation factor for the given filter combination
        filterThickness = self.attState * 30 # thickness in microns
        energy = self.energyMotor.getPosition()
        # print "EscFilters.timeout: energy = ", energy, type(energy)
        # calculate attenuation coefficient for the current energy
        mu_over_rho = math.exp(-2.83482253 * math.log(energy) + 9.78125456)
        self.attFactor = math.exp(-2.7 * (filterThickness / 1e4) * mu_over_rho) * 100
    
        # call the slots manually to force signal emission
        self.attStateChanged(self.attState)
        self.attFactorChanged(self.attFactor)


    def getAttState(self):
        try:
            value= int(self.attState)
        except:
            logging.getLogger("HWR").error('%s: received value on channel is not a integer value', str(self.name()))
            value=None
        return value


    def getAttFactor(self):
        try:
            value = float(self.attFactor)
        except:
            logging.getLogger("HWR").error('%s: received value on channel is not a float value', str(self.name()))
            value=None
        return value


    def attStateChanged(self, channelValue):
        try:
            value = int(channelValue)
        except:
            logging.getLogger("HWR").error('%s: received value on channel is not an integer value', str(self.name())) 
        else:
            self.emit('attStateChanged', (value, ))


    def attFactorChanged(self, channelValue):
        try:
          value = float(channelValue)
        except:
            logging.getLogger("HWR").error('%s: received value on channel is not a float value', str(self.name()))
        else:
            self.emit('attFactorChanged', (value, )) 
            

    def toggle(self, filter_index):
        #print "EscFilters.toggle: filter_index=%s" % filter_index
        attState = self.getAttState()
        #print "EscFilters.toggle: attState=%s" % attState
        obj = self['atte'][filter_index]
        #print "EscFilters.toggle: obj.bits=%s" % obj.bits
        newState = attState ^ obj.bits
        #print "EscFilters.toggle: newState=%s" % newState
        self.setAttState(newState)


    def setTransmission(self, transmission_percent):
        if (transmission_percent == 0):
            transmission_percent = 0.001
        # print "EscFilters.setTransmission: %s" % transmission_percent
        energy = self.energyMotor.getPosition()
        # calculate attenuation coefficient for the current energy
        mu_over_rho = math.exp(-2.83482253 * math.log(energy) + 9.78125456)
        # calculate requested filter thickness in um
        reqFilterThickness = (math.log(transmission_percent / 100.0) / 2.7 / (-mu_over_rho)) * 1e4
        # print "EscFilters.setTransmission: requestedFilterThickness = %s" % reqFilterThickness
        # find the nearest filter position to fit the requested thickness
        # integer division
        reqAttState = int(round(reqFilterThickness / 30.0) * 30) / 30
        if (reqAttState > 127):
            reqAttState = 127
        self.setAttState(reqAttState)


    def setAttState(self, attState):
        reqFilterBlades = []
        for index, item in enumerate(EscFilters.filterNames):
            if (attState & (1 << index)):
               reqFilterBlades.append(1)
            else:
               reqFilterBlades.append(2)
        # print "EscFilters.setAttState: %s" % reqFilterBlades
        self.putXiaFilters(reqFilterBlades)
        
  	      
    def is_in(self, attenuator_index):
        curr_bits = self.getAttState()
        val = self.bits[attenuator_index]
        return bool(val & curr_bits)
