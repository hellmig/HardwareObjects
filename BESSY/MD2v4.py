# from Qub.Tools import QubImageSave
from HardwareRepository.BaseHardwareObjects import Equipment
import tempfile
import logging
import math
import os
import time
from HardwareRepository import HardwareRepository
from HardwareRepository.TaskUtils import *
import MiniDiff
from HardwareRepository import EnhancedPopen
import copy
import gevent
import numpy
from BlissFramework.Utils import terminal_server
import PyTango

class MD2v4(MiniDiff.MiniDiff):

    def init(self):
        self.phiMotor = self.getDeviceByRole('phi')
        self.x_calib = self.getChannelObject("x_calib_attr")
        if self.x_calib is not None:
            self.x_calib.connectSignal("update", self.calibrationFactorsChanged)
        self.y_calib = self.getChannelObject("y_calib_attr")
        self.moveMultipleMotors = self.getCommandObject("sync_move_cmd")
        self.beamPosX = self.getChannelObject("beam_pos_x")
        #if self.beamPosX is not None:
        #    self.beamPosX.connectSignal("update", self.beamPositionChanged)
        self.beamPosY = self.getChannelObject("beam_pos_y")
        self.state = self.getChannelObject("state")
        self.phasePosition = self.getChannelObject("phase_position")
        self.centringClickCmd = self.getCommandObject("centring_click_cmd")
        self.startCentringPhaseCmd = self.getCommandObject("start_centring_phase_cmd")
        self.old_beam_pos = (-1, -1)

        MiniDiff.MiniDiff.init(self)
        self.centringPhiy.direction = -1

        try:
            self.grid_direction = eval(self.getProperty("gridDirection"))
        except:
            self.grid_direction = {"fast": (0, 1), "slow": (1, 0)}
            logging.getLogger("HWR").warning('MD2v4: Grid direction is not defined. Using default.')
        try:
            self.phase_list = eval(self.getProperty("phaseList"))
        except:
            self.phase_list = []  
        self.centring_hwobj = self.getObjectByRole('centring')
        if self.centring_hwobj is None:
            logging.getLogger("HWR").debug('EMBLMinidiff: Centring math is not defined')

        # make the diffractometer object compatible with the new graphics manager
        # in Qt4 implementation
        # ---------------------
        self.start_centring_method = self.startCentringMethod
        self.cancel_centring_method = self.cancelCentringMethod 
        self.image_clicked = self.imageClicked 
        self.accept_centring = self.acceptCentring 
        self.reject_centring = self.rejectCentring 
        self.get_centring_status = self.getCentringStatus 
        self.take_snapshots = self.takeSnapshots 
        self.move_motors = self.moveMotors 
        # ---------------------

        #terminal_server.export("udiff", self)

    #def beamPositionChanged(self, value):
    #    #print "MD2v4.beamPositionChanged", self.beamPosX.getValue(), self.beamPosY.getValue()
    #    self.emit("minidiffReady", ())
    #    #self.emit("minidiffStateChanged", (self.state.getValue()))

    def calibrationFactorsChanged(self, value):
        while (self.old_beam_pos[0] == self.beamPosX.getValue()):
            time.sleep(0.1)
        self.old_beam_pos = (self.beamPosX.getValue(), self.beamPosY.getValue())  
        #print "MD2v4.calibrationFactorsChanged", self.x_calib.getValue(), self.y_calib.getValue(), self.beamPosX.getValue(), self.beamPosY.getValue()
        self.emit("minidiffReady", ())
        self.emit("minidiffStateChanged", (self.zoomMotor.getState()))

    def getBeamPosX(self):
        return self.beamPosX.getValue()

    def getBeamPosY(self):
        return self.beamPosY.getValue()

    def getCalibrationData(self, offset):
        # update of self.pixelsPerMmY, self.pixelsPerMmZ carried out in MiniDiff base class triggered by zoom level update
        return (1000.0/self.x_calib.getValue(), 1000.0/self.y_calib.getValue())

    def emitCentringSuccessful(self):
        # save position in MD2 software
        self.getCommandObject("save_centring_position")()
        # do normal stuff
        return MiniDiff.MiniDiff.emitCentringSuccessful(self)

    def startCentringMethod(self,method,sample_info=None):

        if self.phasePosition.getValue() != 1:
            # centring phase not activated yet

            # wait until MD2 is ready to change the phase
            while self.state.getValue() != PyTango.DevState.STANDBY:
                time.sleep(0.1)
            # activate the sample centring phase before starting the centring procedure
            self.startCentringPhaseCmd()
        
        # do the general centring stuff
        MiniDiff.MiniDiff.startCentringMethod(self, method, sample_info)

    def update_values(self):
        self.emit('zoomMotorPredefinedPositionChanged', None, None)
        omega_ref = [0, 288]
        self.emit('omegaReferenceChanged', omega_ref)

    def get_phase_list(self):
        return self.phase_list

    def get_grid_direction(self):
        """
        Descript. :
        """
        return self.grid_direction

    def in_plate_mode(self):
	return False

    def take_snapshots(self, image_count, wait = False):
        """
        Descript. :
        """

        return

    def takeSnapshots(self, image_count, wait = False):
        """
        Descript. :
        """

        return

