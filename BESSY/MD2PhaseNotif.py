"""
Name: 		MD2PhaseNotif
Author: 	Michael Hellmig
Organization: 	Helmholtz-Zentrum Berlin fuer Materialien und Energie GmBH

Description:
Bliss Framework Hardware Object to propagate the >Phase< Status of a Maatel Micro-Diffractometer (MD2) to Bliss Framework Bricks,
e. g. to activate/deactivate certain functionality in particular phases of the MD2 (current only used for CryoShutterBrick)
"""

import logging
import os
import stat
from HardwareRepository.BaseHardwareObjects import Equipment 
from PyTango import DevState

class MD2PhaseNotif(Equipment):
    def init(self):
        phase_chan = self.addChannel({ 'type': 'tango', 'name': 'phasePosition','polling':1000 }, "PhasePosition")
        phase_chan.connectSignal("update", self.phasePositionChanged)

    def phasePositionChanged(self, phase):
        self.emit("phaseChanged", (str(phase), ))

    def getPhasePosition(self):
        phase_chan = self.getChannelObject("phasePosition")
        return phase_chan.getValue()

