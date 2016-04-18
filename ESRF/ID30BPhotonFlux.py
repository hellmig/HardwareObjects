from HardwareRepository.BaseHardwareObjects import Equipment
from HardwareRepository.TaskUtils import *
import numpy
import time
import logging

class ID30BPhotonFlux(Equipment):
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)

    def init(self):
        self.controller = self.getObjectByRole("controller")
        self.shutter = self.getDeviceByRole("shutter")
        self.energy_motor = self.getObjectByRole("energy")
        try:
            self.aperture = self.getObjectByRole("aperture")
        except:
            self.aperture = None
        try:
            fname  = self.getProperty("calibrated_diodes_file")
        except:
            pass
        self.flux_calc = self.controller.CalculateFlux()
        self.flux_calc.init(fname)
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
        try:
            counts = self.controller.i0.read()
            if counts == -9999 :
                counts = 0
        except:
            counts = 0
            logging.getLogger("HWR").exception("%s: could not get counts", self.name())
        try:
          egy = self.energy_motor.getCurrentEnergy()*1000.0
          calib = self.flux_calc.calc_flux_coef(egy)
        except:
          logging.getLogger("HWR").exception("%s: could not get energy", self.name())
        else:
            if self.aperture is None:
                aperture_coef = 1
            else:
                try:
                    aperture_coef = self.aperture.getApertureCoef()
                except:
                    aperture_coef = 1
            counts = abs(counts * calib[0] * aperture_coef)
        return counts

    def connectNotify(self, signal):
        if signal == "valueChanged":
          self.emitValueChanged()

    def shutterStateChanged(self, _):
        self.countsUpdated(self._get_counts())

    def updateFlux(self, _):
        self.countsUpdated(self._get_counts(), ignore_shutter_state=False)

    def countsUpdated(self, counts, ignore_shutter_state=False):
        if not ignore_shutter_state and self.shutter.getShutterState()!="opened":
          self.emitValueChanged(0)
          return
        flux = counts
        self.emitValueChanged("%1.3g" % flux)

    def getCurrentFlux(self):
        self.updateFlux("dummy")
        return self.current_flux

    def emitValueChanged(self, flux=None):
        if flux is None:
          self.current_flux = None
          self.emit("valueChanged", ("?", ))
        else:
          self.current_flux = flux
          self.emit("valueChanged", (self.current_flux, ))
