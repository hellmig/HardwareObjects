from HardwareRepository.BaseHardwareObjects import Equipment
import logging
from qt import *

class PhotonFluxDummy(Equipment):
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)

    def init(self):
        self.dummy_flux = 1e11

        try:
          self.shutter = self.getDeviceByRole("shutter")
        except:
          logging.getLogger("HWR").exception("%s: could not find shutter device in the hardware repository.", self.name())

        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL('timeout()'), self.timerSignal)
        self.timer.start(1000)


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


    def timerSignal(self):
        self.countsUpdated(self.dummy_flux)
