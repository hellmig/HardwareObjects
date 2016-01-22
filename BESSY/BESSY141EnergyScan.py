from BESSYEnergyScan import *
import logging

class BESSY141EnergyScan(BESSYEnergyScan):
    def __init__(self, name):
        print "BESSY141EnergyScan.__init__"
        BESSYEnergyScan.__init__(self, name, TunableEnergy())

    @task
    def energy_scan_hook(self, energy_scan_parameters):
        # try:
        #     BESSYEnergyScan.move_energy(self,energy_scan_parameters['findattEnergy'])
        # except:
        #     pass
        pass

    @task
    def move_undulators(self, gaps):
        pass
      
    def calculate_und_gaps(self, energy, undulator="u21d"):
        pass

    @task
    def set_mca_roi(self, eroi_min, eroi_max):
        # self.execute_command("calculateMcaRoi",eroi_min, eroi_max)
        pass

    @task
    def choose_attenuation(self):
        # self.execute_command("chooseAttenuation")
        # self.energy_scan_parameters["transmissionFactor"] = self.transmission.getAttFactor()
        pass

    @task
    def execute_energy_scan(self, energy_scan_parameters):
        element = energy_scan_parameters["element"]
        edge = energy_scan_parameters["edge"]
        self.execute_command("executeScan", "%s %s" % (element, edge))
        
    def canScanEnergy(self):
        return True

    def canMoveEnergy(self):
        return self.canScanEnergy()
