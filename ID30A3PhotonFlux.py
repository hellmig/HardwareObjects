from HardwareRepository.BaseHardwareObjects import Equipment
from HardwareRepository.TaskUtils import *
import numpy
import time
import logging

class ID30A3PhotonFlux(Equipment):
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)

    def init(self):
        controller = self.getObjectByRole("controller")
        self.musst = controller.musst
        self.energy_motor = self.getDeviceByRole("energy")
        self.shutter = self.getDeviceByRole("shutter")
        self.factor = self.getProperty("current_photons_factor")

        self.shutter.connect("shutterStateChanged", self.shutterStateChanged)

        self.counts_reading_task = self._read_counts_task(wait=False)

    @task
    def _read_counts_task(self):
        old_counts = None
        while True:
            counts = self._get_counts()
            if counts != old_counts:
                old_counts = counts
                self.countsUpdated(counts)
            time.sleep(1)

    def _get_counts(self):
        counts = -100*int(self.musst.putget("#?CH CH6").split()[0])/float(0x7FFFFFFF)
        if counts < 0:
            counts = 0
        return counts

    def connectNotify(self, signal):
        if signal == "valueChanged":
          self.emitValueChanged()

    def shutterStateChanged(self, _):
        self.countsUpdated(self._get_counts())

    def updateFlux(self, _):
        self.countsUpdated(self._get_counts(), ignore_shutter_state=True)

    def countsUpdated(self, counts, ignore_shutter_state=False):
        if not ignore_shutter_state and self.shutter.getShutterState()!="opened":
          self.emitValueChanged(0)
          return
        flux = counts * self.factor
        self.emitValueChanged("%1.3g" % flux)

        """ 
        try:
          counts = counts[self.index]
        except TypeError:
          logging.getLogger("HWR").error("%s: counts is None", self.name())
          return
        flux = None

        try:
          egy = self.energy_motor.getPosition()*1000.0
        except:
          logging.getLogger("HWR").exception("%s: could not get energy", self.name())
        else:
          try:
            calib_dict = self.calibration_chan.getValue()
            if calib_dict is None:
              logging.getLogger("HWR").error("%s: calibration is None", self.name())
            else:
              calibs = [(float(c["energy"]), float(c[self.counter])) for c in calib_dict.itervalues()]
              calibs.sort()
              E = [c[0] for c in calibs]
              C = [c[1] for c in calibs]
          except:
            logging.getLogger("HWR").exception("%s: could not get calibration", self.name())
          else:
            try:
              aperture_coef = self.aperture.getApertureCoef()
            except:
              aperture_coef = 1
            if aperture_coef <= 0:
              aperture_coef = 1
            calib = numpy.interp([egy], E, C)
            flux = counts * calib * aperture_coef
            #logging.getLogger("HWR").debug("%s: flux-> %f * %f=%f , calib_dict=%r", self.name(), counts, calib, counts*calib, calib_dict)
            self.emitValueChanged("%1.3g" % flux)
        """

    def getCurrentFlux(self):
        return self.current_flux

    def emitValueChanged(self, flux=None):
        if flux is None:
          self.current_flux = None
          self.emit("valueChanged", ("?", ))
        else:
          self.current_flux = flux
          self.emit("valueChanged", (self.current_flux, ))
