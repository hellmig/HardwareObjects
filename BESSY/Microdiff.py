from HardwareRepository.BaseHardwareObjects import Equipment
import tempfile
import logging
import math
import os
import time
from HardwareRepository import HardwareRepository
import MiniDiff
from HardwareRepository import EnhancedPopen
import copy
import gevent
import sample_centring

class DiffractometerState:
    """
    Enumeration of diffractometer states
    """
    Created      = 0
    Initializing = 1
    On           = 2
    Off          = 3
    Closed       = 4
    Open         = 5
    Ready        = 6
    Busy         = 7
    Moving       = 8
    Standby      = 9
    Running      = 10
    Started      = 11
    Stopped      = 12
    Paused       = 13
    Remote       = 14
    Reset        = 15
    Closing      = 16
    Disable      = 17
    Waiting      = 18
    Positioned   = 19
    Starting     = 20
    Loading      = 21
    Unknown      = 22
    Alarm        = 23
    Fault        = 24
    Invalid      = 25
    Offline      = 26

    STATE_DESC = {Created: "Created",
                  Initializing: "Initializing",
                  On: "On",
                  Off: "Off",
                  Closed: "Closed",
                  Open: "Open",
                  Ready: "Ready",
                  Busy: "Busy",
                  Moving: "Moving",
                  Standby: "Standby",
                  Running: "Running",
                  Started: "Started",
                  Stopped: "Stopped",
                  Paused: "Paused",
                  Remote: "Remote",
                  Reset: "Reset",
                  Closing : "Closing",
                  Disable: "Disable",
                  Waiting: "Waiting",
                  Positioned: " Positioned",
                  Starting: "Starting",
                  Loading: "Loading",
                  Unknown: "Unknown",
                  Alarm: "Alarm",
                  Fault: "Fault",
                  Invalid: "Invalid",
                  Offline: "Offline"}

    @staticmethod
    def tostring(state):
        return DiffractometerState.STATE_DESC.get(state, "Unknown")

MICRODIFF = None

class Microdiff(MiniDiff.MiniDiff):
    def init(self):
        global MICRODIFF
        MICRODIFF = self
        self.timeout = 3
        self.phiMotor = self.getDeviceByRole('phi')
        self.exporter_addr = self.phiMotor.exporter_address
        self.x_calib = self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name":"x_calib" }, "CoaxCamScaleX")
        self.y_calib = self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name":"y_calib" }, "CoaxCamScaleY")       
        self.moveMultipleMotors = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"move_multiple_motors" }, "SyncMoveMotors")
        self.head_type = self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name":"head_type" }, "HeadType")
        self.kappa = self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name":"kappa_enable" }, "KappaIsEnabled") 
        self.phases = {"Centring":1, "BeamLocation":2, "DataCollection":3, "Transfer":4}
        self.movePhase = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"move_to_phase" }, "startSetPhase")
        self.readPhase =  self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name":"read_phase" }, "CurrentPhase")
        self.scanLimits = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"scan_limits" }, "getOmegaMotorDynamicScanLimits")
        if self.getProperty("use_hwstate"):
            self.hwstate_attr = self.addChannel({"type":"exporter", "exporter_address": self.exporter_addr, "name":"hwstate" }, "HardwareState")
        else:
            self.hwstate_attr = None
        self.swstate_attr = self.addChannel({"type":"exporter", "exporter_address": self.exporter_addr, "name":"swstate" }, "State")
        # self.swstate_attr = self.getChannelObject("state")
        if self.swstate_attr is not None:
            self.current_state = self.swstate_attr.getValue()
            self.swstate_attr.connectSignal("update", self.swstate_attr_changed)

        # self.beamPosX = self.addChannel({"type": "tango", "name": "beam_pos_x", "tangoname": "bl141/microdiff/general", "polling": "events"}, "BeamPositionHorizontal")
        # self.beamPosY = self.addChannel({"type": "tango", "name": "beam_pos_y", "tangoname": "bl141/microdiff/general", "polling": "events"}, "BeamPositionVertical")
        self.beamPosX = self.addChannel({"type":"exporter", "exporter_address":self.exporter_addr, "name": "beam_pos_x"}, "BeamPositionHorizontal")
        self.beamPosY = self.addChannel({"type":"exporter", "exporter_address":self.exporter_addr, "name": "beam_pos_y"}, "BeamPositionVertical")
        
        MiniDiff.MiniDiff.init(self)
        self.centringPhiy.direction = -1

        try:
            self.grid_direction = eval(self.getProperty("gridDirection"))
        except:
            self.grid_direction = {"fast": (0, 1), "slow": (1, 0)}
            logging.getLogger("HWR").warning('Microdiff: Grid direction is not defined. Using default.')
        try:
            self.phase_list = eval(self.getProperty("phaseList"))
        except:
            self.phase_list = []  

        self.MOTOR_TO_EXPORTER_NAME = self.getMotorToExporterNames()

        self.current_state = None

#        self.chan_state = self.getChannelObject('State')
#        if self.chan_state:
#            self.current_state = self.chan_state.getValue()
#            self.chan_state.connectSignal("update", self.state_changed)

        self.chan_current_phase = self.getChannelObject('CurrentPhase')
        if self.chan_current_phase is not None:
            self.connect(self.chan_current_phase, "update", self.current_phase_changed)

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
        # self.is_ready = self.isReady
        # ---------------------


    def getMotorToExporterNames(self):
        #only temporary. Get the names from the xml files
        MOTOR_TO_EXPORTER_NAME = {"focus":"AlignmentX", "kappa":"Kappa",
                                  "kappa_phi":"Phi", "phi": "Omega",
                                  "phiy":"AlignmentY", "phiz":"AlignmentZ",
                                  "sampx":"CentringX", "sampy":"CentringY",
                                  "zoom":"Zoom"}
        return MOTOR_TO_EXPORTER_NAME


    def getMotorToExporterNames(self):
        #only temporary. Get the names from the xml files
        MOTOR_TO_EXPORTER_NAME = {"focus":"AlignmentX", "kappa":"Kappa",
                                  "kappa_phi":"Phi", "phi": "Omega",
                                  "phiy":"AlignmentY", "phiz":"AlignmentZ",
                                  "sampx":"CentringX", "sampy":"CentringY",
                                  "zoom":"Zoom"}
        return MOTOR_TO_EXPORTER_NAME
 
    def getBeamPosX(self):
        return self.beamPosX.getValue()

    def getBeamPosY(self):
        return self.beamPosY.getValue()

    def getCalibrationData(self, offset):
        return (1.0/self.x_calib.getValue(), 1.0/self.y_calib.getValue())

    def emitCentringSuccessful(self):
        #check first if all the motors have stopped
        self._wait_ready(10)

        # save position in MD2 software
        self.getCommandObject("save_centring_positions")()
 
        # do normal stuff
        return MiniDiff.MiniDiff.emitCentringSuccessful(self)

    def swstate_attr_changed(self, value):
        # print "Microdiff.swstate_attr_changed", value, type(value)
        self.current_state = value
        # if value == PyTango.DevState.STANDBY:
        #    while not self.isReady():
        #        #print "waiting"
        #        time.sleep(0.1)
        self.emit("stateChanged", (self.current_state,))
        self.emit("minidiffStateChanged", (self.current_state,))
        self.emit("minidiffStatusChanged", (self.current_state,))

    def _ready(self):
        if self.hwstate_attr:
            if self.hwstate_attr.getValue() == "Ready" and self.swstate_attr.getValue() == "Ready":
                return True
        else:
            if self.swstate_attr.getValue() == "Ready":
                return True
        return False

    def _wait_ready(self, timeout=None):
        if timeout <= 0:
            timeout = self.timeout
        tt1 = time.time()
        while time.time() - tt1 < timeout:
             if self._ready():
                 break
             else:
                 time.sleep(0.5)

    def moveToPhase(self, phase, wait=False, timeout=None):
        if self._ready():
            if self.phases.has_key(str(phase)):
                self.movePhase(str(phase))
                if wait:
                    if not timeout:
                        timeout = 40
                    self._wait_ready(timeout)
        else:
            print "moveToPhase - Ready is: ", self._ready()
    
    def getPhase(self):
        return self.readPhase.getValue()

    def moveSyncMotors(self, motors_dict, wait=False, timeout=None):
        argin = ""
        #print "start moving motors =============", time.time()
        for motor in motors_dict.keys():
            position = motors_dict[motor]
            if position is None:
                continue
            name=self.MOTOR_TO_EXPORTER_NAME[motor]
            argin += "%s=%0.3f;" % (name, position)
        if not argin:
            return
        move_sync_motors = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"move_sync_motors" }, "startSimultaneousMoveMotors")
        move_sync_motors(argin)

        if wait:
            while not self._ready():
                time.sleep(0.5)
        #print "end moving motors =============", time.time()
            
    def oscilScan(self, start, end, exptime, wait=False):
        if self.in_plate_mode():
            scan_speed = math.fabs(end-start) / exptime
            low_lim, hi_lim = map(float, self.scanLimits(scan_speed))
            if start < low_lim:
                raise ValueError("Scan start below the allowed value %f" % low_lim)
            elif end > hi_lim:
                raise ValueError("Scan end abobe the allowed value %f" % hi_lim)

        scan_params = "1\t%0.3f\t%0.3f\t%0.4f\t1"% (start, (end-start), exptime)
        scan = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"start_scan" }, "startScanEx")
        scan(scan_params)
        print "scan started at ----------->", time.time()
        if wait:
            self._wait_ready(300) #timeout of 5 min
            print "finished at ---------->", time.time()

    def oscilScan4d(self, start, end, exptime,  motors_pos, wait=False):
        if self.in_plate_mode():
            scan_speed = math.fabs(end-start) / exptime
            low_lim, hi_lim = map(float, self.scanLimits(scan_speed))
            if start < low_lim:
                raise ValueError("Scan start below the allowed value %f" % low_lim)
            elif end > hi_lim:
                raise ValueError("Scan end abobe the allowed value %f" % hi_lim)
                
        scan_params = "%0.3f\t%0.3f\t%f\t"% (start, (end-start), exptime)
        scan_params += "%0.3f\t" % motors_pos['1']['phiy']
        scan_params += "%0.3f\t" % motors_pos['1']['phiz']
        scan_params += "%0.3f\t" % motors_pos['1']['sampx']
        scan_params += "%0.3f\t" % motors_pos['1']['sampy']
        scan_params += "%0.3f\t" % motors_pos['2']['phiy']
        scan_params += "%0.3f\t" % motors_pos['2']['phiz']
        scan_params += "%0.3f\t" % motors_pos['2']['sampx']
        scan_params += "%0.3f" % motors_pos['2']['sampy']

        scan = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"start_scan4d" }, "startScan4DEx")
        scan(scan_params)
        print "scan started at ----------->", time.time()
        if wait:
            self._wait_ready(900) #timeout of 15 min
            print "finished at ---------->", time.time()

    def in_plate_mode(self):
        try:
            return self.head_type.getValue() == "Plate"
        except:
            return False

    def in_kappa_mode(self):
        return self.head_type.getValue() == "MiniKappa" and self.kappa.getValue()

    def getPositions(self):
        pos = { "phi": float(self.phiMotor.getPosition()),
                "focus": float(self.focusMotor.getPosition()),
                "phiy": float(self.phiyMotor.getPosition()),
                "phiz": float(self.phizMotor.getPosition()),
                "sampx": float(self.sampleXMotor.getPosition()),
                "sampy": float(self.sampleYMotor.getPosition()), "zoom": float(self.zoomMotor.getPosition())}
        if self.in_kappa_mode() == True:
            pos.update({"kappa": float(self.kappaMotor.getPosition()), "kappa_phi": float(self.kappaPhiMotor.getPosition())})
        return pos

    def moveMotors(self, roles_positions_dict):
        if not self.in_kappa_mode():
            try:
                roles_positions_dict.pop["kappa"]
                roles_positions_dict.pop["kappa_phi"]
            except:
                pass
            
        self.moveSyncMotors(roles_positions_dict, wait=True)

    def start3ClickCentring(self, sample_info=None):
        if self.in_plate_mode():
            plateTranslation = self.getDeviceByRole('plateTranslation')
            cmd_set_plate_vertical = self.addCommand({"type":"exporter", "exporter_address":self.exporter_addr, "name":"plate_vertical" }, "setPlateVertical")
            low_lim, high_lim = self.phiMotor.getDynamicLimits()
            phi_range = math.fabs(high_lim - low_lim -1)

            self.currentCentringProcedure = sample_centring.start_plate({"phi":self.centringPhi,
                                                                         "phiy":self.centringPhiy,
                                                                         "sampx": self.centringSamplex,
                                                                         "sampy": self.centringSampley,
                                                                         "phiz": self.centringPhiz,
                                                                         "plateTranslation": plateTranslation}, 
                                                                        self.pixelsPerMmY, self.pixelsPerMmZ, 
                                                                        self.getBeamPosX(), self.getBeamPosY(),
                                                                        cmd_set_plate_vertical,
                                                                        phi_range = phi_range,lim_pos=high_lim-0.5)
        else:
            self.currentCentringProcedure = sample_centring.start({"phi":self.centringPhi,
                                                                   "phiy":self.centringPhiy,
                                                                   "sampx": self.centringSamplex,
                                                                   "sampy": self.centringSampley,
                                                                   "phiz": self.centringPhiz }, 
                                                                  self.pixelsPerMmY, self.pixelsPerMmZ, 
                                                                  self.getBeamPosX(), self.getBeamPosY())
                                                                         
        self.currentCentringProcedure.link(self.manualCentringDone)

    def update_values(self):
        self.emit('zoomMotorPredefinedPositionChanged', None, None)
        omega_ref = [0, 288]
        self.emit('omegaReferenceChanged', omega_ref)
        self.emit('minidiffPhaseChanged', (self.current_phase, ))

    def get_phase_list(self):
        return self.phase_list

    def set_phase(self, phase, timeout=None):
        """
        Description:
        """
        self.moveToPhase(phase, False, timeout)

    def get_grid_direction(self):
        """
        Descript. :
        """
        return self.grid_direction

    def is_ready(self):
        """
        Detects if device is ready
        """
        return self.current_state == DiffractometerState.tostring(\
                    DiffractometerState.Ready)

#    def state_changed(self, state):
#        self.current_state = state
#        self.emit("minidiffStateChanged", (self.current_state))
#        self.emit("minidiffStatusChanged", (self.current_state))

    def current_phase_changed(self, current_phase):
        """
        Descript. :
        """
        self.current_phase = current_phase
        #logging.getLogger("HWR").info("Current_phase_changed to %s" % current_phase)
        self.emit('minidiffPhaseChanged', (current_phase, ))

    def zoomMotorPredefinedPositionChanged(self, positionName=None, offset=None):
        MiniDiff.MiniDiff.zoomMotorPredefinedPositionChanged(self, positionName, offset)
        self.emit("pixelsPerMmChanged", (self.getCalibrationData(offset),))

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

    def move_to_beam(self, x, y):
        # logging.getLogger("HWR").info("Microdiff: \"move to beam\" functionality not implemented yet.")
        MiniDiff.MiniDiff.moveToBeam(self, x, y)

def set_light_in(light, light_motor, zoom):
    MICRODIFF.getDeviceByRole("flight").move(0)
    MICRODIFF.getDeviceByRole("lightInOut").actuatorIn()

MiniDiff.set_light_in = set_light_in
