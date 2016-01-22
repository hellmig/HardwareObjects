from HardwareRepository.BaseHardwareObjects import Equipment
import logging
import gevent
from HardwareRepository.TaskUtils import *


class PhotonFluxDummy(Equipment):
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        task1000ms=self.__timer_1000ms_task(wait=False)
        task1000ms.link(self._onTimer1000msExit)

    def init(self):
        self.dummy_flux = 1e11

        try:
          self.shutter = self.getDeviceByRole("shutter")
        except:
          logging.getLogger("HWR").exception("%s: could not find shutter device in the hardware repository.", self.name())

    def _onTimer1000msExit(self, task):
        logging.warning("Exiting PhotonFluxDummy timer task")
        
    @task
    def __timer_1000ms_task(self, *args):
        while(True):
            gevent.sleep(1.0)
            self._onTimer1000ms()

    def _onTimer1000ms(self):
        self.timeout()

    def timeout(self):
        self.countsUpdated(self.dummy_flux)

    def connectNotify(self, signal):
        if signal == "valueChanged":
          self.emitValueChanged()

    def updateFlux(self, _):
        self.countsUpdated(self.dummy_flux, ignore_shutter_state=True)

    def countsUpdated(self, counts, ignore_shutter_state=False):
        if not ignore_shutter_state and self.shutter.getShutterState() != "opened":
          self.emitValueChanged(0)
          return

        flux = counts
        self.emitValueChanged("%1.3g" % flux)

    def emitValueChanged(self, counts=None):
        if counts is None:
          self.emit("valueChanged", ("?", ))
        else:
          self.emit("valueChanged", (counts, ))

    def getCurrentFlux(self):
        return self.dummy_flux
