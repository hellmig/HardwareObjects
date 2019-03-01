"""
BESSY141Microdiff hardware object

Derived from BIOMAXMD3.py, see also for documentation etc.
"""

import time
import gevent
import logging

from math import sqrt

try:
    import lucid2 as lucid
except ImportError:
    try:
        import lucid
    except ImportError:
        logging.warning("Could not find autocentring library, " + \
                        "automatic centring is disabled")

from GenericDiffractometer import GenericDiffractometer
from HardwareRepository.TaskUtils import *

class BESSY141Microdiff(GenericDiffractometer):

    MOTOR_TO_EXPORTER_NAME = {"focus": "AlignmentX", "kappa": "Kappa",
                              "kappa_phi": "Phi", "phi": "Omega",
                              "phiy": "AlignmentY", "phiz":"AlignmentZ",
                              "sampx": "CentringX", "sampy": "CentringY",
                              "zoom": "Zoom"}

    AUTOMATIC_CENTRING_IMAGES = 6

    def __init__(self, *args):
        """
        Description:
        """
        GenericDiffractometer.__init__(self, *args)

        # Hardware objects ---------------------------------------------------- 
        self.camera_hwobj = None
        self.omega_reference_motor = None
        self.centring_hwobj = None

        # create shorter references to the motor objects
        self.phi_motor_hwobj = None
        self.phiz_motor_hwobj = None
        self.phiy_motor_hwobj = None
        self.zoom_motor_hwobj = None
        self.focus_motor_hwobj = None
        self.sample_x_motor_hwobj = None
        self.sample_y_motor_hwobj = None

        self.detector_distance_motor_hwobj = None

        self.front_light_hwobj = None
        self.back_light_hwobj = None
        self.back_light_switch_hwobj = None
        self.front_light_switch_hwobj = None

        # 2019-02-12-bessy-mh:
        self.minikappa_correction_hwobj = None

        # Channels and commands -----------------------------------------------
        self.chan_scintillator_position = None
        self.chan_capillary_position = None

        # Internal values -----------------------------------------------------
        self.use_sc = False
        self.omega_reference_pos = [0, 0]

        # 2017-09-20-bessy-mh: add dummy dict and method to make current GenericDiffractometer
        #                      happy, to be removed after update with improved
        #                      GenericDiffractometer implementation
        self.cancel_centring_methods = {
            GenericDiffractometer.CENTRING_METHOD_MANUAL: self.cancel_centring_method_dummy,
            GenericDiffractometer.CENTRING_METHOD_AUTO: self.cancel_centring_method_dummy,
            GenericDiffractometer.CENTRING_METHOD_MOVE_TO_BEAM: self.cancel_centring_method_dummy
        }
       
    def init(self):
        """
        Description:
        """
        GenericDiffractometer.init(self)
        self.centring_status = {"valid": False}
        self.exporter_addr = self.getProperty("exporter_address")

        self.chan_state = self.getChannelObject('State')
        self.current_state = self.chan_state.getValue()
        self.chan_state.connectSignal("update", self.state_changed)

        self.chan_calib_x = self.getChannelObject('CoaxCamScaleX')
        self.chan_calib_y = self.getChannelObject('CoaxCamScaleY')
        self.update_pixels_per_mm()

        self.chan_head_type = self.getChannelObject('HeadType')
        self.head_type = self.chan_head_type.getValue()

        self.chan_current_phase = self.getChannelObject('CurrentPhase')
        self.connect(self.chan_current_phase, "update", self.current_phase_changed)

        self.chan_fast_shutter_is_open = self.getChannelObject('FastShutterIsOpen')
        self.chan_fast_shutter_is_open.connectSignal("update", self.fast_shutter_state_changed)
       
        self.chan_scintillator_position = self.getChannelObject('ScintillatorPosition')
        self.chan_capillary_position = self.getChannelObject('CapillaryPosition')

        self.cmd_start_set_phase = self.getCommandObject('startSetPhase')
        self.cmd_move_sync_motors = self.getCommandObject('startSimultaneousMoveMotors')
        # self.cmd_start_auto_focus = self.getCommandObject('startAutoFocus')
        # self.cmd_get_omega_scan_limits = self.getCommandObject('getOmegaMotorDynamicScanLimits')
        self.cmd_save_centring_positions = self.getCommandObject('saveCentringPositions')
        self.cmd_abort = self.getCommandObject('abort')
      
        # front and back light not implemented yet
        self.front_light_hwobj = self.getObjectByRole('frontlight')
        self.back_light_hwobj = self.getObjectByRole('backlight')
        self.back_light_switch_hwobj = self.getObjectByRole('backlightswitch')
        self.front_light_switch_hwobj = self.getObjectByRole('frontlightswitch')

        self.centring_hwobj = self.getObjectByRole('centring')
        if self.centring_hwobj is None:
            logging.getLogger("HWR").debug('BESSY141Microdiff: Centring math is not defined')
      
        # create shorter references to the motor objects
        self.phi_motor_hwobj = self.motor_hwobj_dict['phi']
        self.focus_motor_hwobj = self.motor_hwobj_dict['focus']
        self.phiz_motor_hwobj = self.motor_hwobj_dict['phiz']
        self.phiy_motor_hwobj = self.motor_hwobj_dict['phiy']
        self.sample_x_motor_hwobj = self.motor_hwobj_dict['sampx']
        self.sample_y_motor_hwobj = self.motor_hwobj_dict['sampy']

        self.connect(self.motor_hwobj_dict['phi'], "positionChanged", self.phi_motor_moved) 
        self.connect(self.motor_hwobj_dict['focus'], "positionChanged", self.focus_motor_moved)
        self.connect(self.motor_hwobj_dict['phiy'],"positionChanged", self.phiy_motor_moved)
        self.connect(self.motor_hwobj_dict['phiz'], "positionChanged", self.phiz_motor_moved)
        self.connect(self.motor_hwobj_dict['kappa'], "positionChanged", self.kappa_motor_moved)
        self.connect(self.motor_hwobj_dict['kappa_phi'], "positionChanged", self.kappa_phi_motor_moved)
        self.connect(self.motor_hwobj_dict['sampx'], "positionChanged",  self.sampx_motor_moved)
        self.connect(self.motor_hwobj_dict['sampy'], "positionChanged", self.sampy_motor_moved)

        self.zoom_motor_hwobj = self.motor_hwobj_dict['zoom']
        self.connect(self.zoom_motor_hwobj, 'positionChanged', self.zoom_position_changed)
        self.connect(self.zoom_motor_hwobj,'predefinedPositionChanged', self.zoom_motor_predefined_position_changed)

    	try:
	    use_sc = self.getProperty("use_sample_changer")
	    self.set_use_sc(use_sc)
	except:
            logging.getLogger("HWR").debug('Cannot set sc mode, use_sc: ', str(use_sc))

    def wait_device_ready(self, timeout=10):
        """ Waits when diffractometer status is ready:
        :param timeout: timeout in second
        :type timeout: int
        """
        with gevent.Timeout(timeout, Exception("Timeout waiting for device ready")):
            while not self.is_ready():
                gevent.sleep(0.01)

    def beam_position_changed(self, value):
        # print "BESSY141Microdiff.beam_position_changed", value
        self.beam_position = value

    def current_phase_changed(self, current_phase):
        """
        Descript. :
        """
        self.current_phase = current_phase
        self.emit('minidiffPhaseChanged', (current_phase, ))

    def state_changed(self, state):
        # logging.getLogger("HWR").debug("State changed: %s" %str(state))
        self.current_state = state
        self.emit("stateChanged", (self.current_state,))
        self.emit("minidiffStateChanged", (self.current_state))
        self.emit("minidiffStatusChanged", (self.current_state))

    def zoom_position_changed(self, value):
        self.update_pixels_per_mm()
        self.current_motor_positions["zoom"] = value
        # self.refresh_omega_reference_position()

    def zoom_motor_predefined_position_changed(self, position_name, offset):
        self.update_pixels_per_mm()
        self.emit('zoomMotorPredefinedPositionChanged',
               (position_name, offset, ))

    def fast_shutter_state_changed(self, is_open):
        """
        Description:
        """
        self.fast_shutter_is_open = is_open
        if is_open:
            msg = "Opened"
        else:
            msg = "Closed"
        self.emit('minidiffShutterStateChanged', (self.fast_shutter_is_open, msg))

    def phi_motor_moved(self, pos):
        """
        Descript. :
        """
        self.current_motor_positions["phi"] = pos
        self.emit("phiMotorMoved", pos)

    def focus_motor_moved(self, pos):
        self.current_motor_positions["focus"] = pos

    def phiy_motor_moved(self, pos):
        self.current_motor_positions["phiy"] = pos

    def phiz_motor_moved(self, pos):
        self.current_motor_positions["phiz"] = pos

    def sampx_motor_moved(self, pos):
        self.current_motor_positions["sampx"] = pos

    def sampy_motor_moved(self, pos):
        self.current_motor_positions["sampy"] = pos

    def kappa_motor_moved(self, pos):
        """
        Descript. :
        """
        self.current_motor_positions["kappa"] = pos
        if time.time() - self.centring_time > 1.0:
            self.invalidate_centring()
        self.emit_diffractometer_moved()
        self.emit("kappaMotorMoved", pos)

    def kappa_phi_motor_moved(self, pos):
        """
        Descript. :
        """
        self.current_motor_positions["kappa_phi"] = pos
        if time.time() - self.centring_time > 1.0:
            self.invalidate_centring()
        self.emit_diffractometer_moved()
        self.emit("kappaPhiMotorMoved", pos)

    def update_pixels_per_mm(self, *args):
        """
        Descript. :
        """
        if self.chan_calib_x:
            self.pixels_per_mm_x = 1.0 / self.chan_calib_x.getValue()
            self.pixels_per_mm_y = 1.0 / self.chan_calib_y.getValue()
            self.emit('pixelsPerMmChanged', ((self.pixels_per_mm_x, 
                                              self.pixels_per_mm_y),))

    def emit_diffractometer_moved(self, *args):
        """
        Descript. :
        """
        self.emit("diffractometerMoved", ())

    def invalidate_centring(self):
        """
        Descript. :
        """   
        if self.current_centring_procedure is None \
         and self.centring_status["valid"]:
            self.centring_status = {"valid": False}
            self.emit_progress_message("")
            self.emit('centringInvalid', ())

    def get_centred_point_from_coord(self, x, y, return_by_names=None):
        """
        Descript. :
        """
        self.centring_hwobj.initCentringProcedure()
        self.centring_hwobj.appendCentringDataPoint({
                   "X" : (x - self.beam_position[0]) / self.pixels_per_mm_x,
                   "Y" : (y - self.beam_position[1]) / self.pixels_per_mm_y})
        # self.omega_reference_add_constraint()
        pos = self.centring_hwobj.centeredPosition()  
        if return_by_names:
            pos = self.convert_from_obj_to_name(pos)
        return pos

    def move_to_beam(self, x, y, omega=None):
        """
        Descript. : function to create a centring point based on all motors
                    positions.
        """  
        if self.current_phase != "BeamLocation":
            GenericDiffractometer.move_to_beam(self, x, y, omega) 
        else:
            logging.getLogger("HWR").debug("Diffractometer: Move to screen" +\
               " position disabled in BeamLocation phase.")

    def manual_centring(self):
        """
        Descript. :
        """
        self.centring_hwobj.initCentringProcedure()
        #self.head_type = self.chan_head_type.getValue()
        for click in range(3):
            self.user_clicked_event = gevent.event.AsyncResult()
            x, y = self.user_clicked_event.get()
            self.centring_hwobj.appendCentringDataPoint(
                 {"X": (x - self.beam_position[0])/ self.pixels_per_mm_x,
                  "Y": (y - self.beam_position[1])/ self.pixels_per_mm_y})
            if self.in_plate_mode():
                #dynamic_limits = self.phi_motor_hwobj.getDynamicLimits()
                dynamic_limits = self.get_osc_limits()
                if click == 0:
                    self.phi_motor_hwobj.move(dynamic_limits[0] + 0.5)
                elif click == 1:
                    self.phi_motor_hwobj.move(dynamic_limits[1] - 0.5)
                
                #elif click == 2:
                #    self.phi_motor_hwobj.move((dynamic_limits[0] + \
                #                                       dynamic_limits[1]) / 2.)
            else:
                if click < 2:
                    self.phi_motor_hwobj.moveRelative(90)
        # self.omega_reference_add_constraint()
        centred_pos_dir = self.centring_hwobj.centeredPosition(return_by_name=False)
        return centred_pos_dir

    def automatic_centring(self):
        """Automatic centring procedure. Rotates n times and executes
           centring algorithm. Optimal scan position is detected.
        """
        self.wait_device_ready(20) 
        surface_score_list = []
        self.zoom_motor_hwobj.moveToPosition("Zoom 1")
        self.wait_device_ready(3)
        self.centring_hwobj.initCentringProcedure()
        for image in range(BESSY141Microdiff.AUTOMATIC_CENTRING_IMAGES):
            x, y, score = self.find_loop()
            if x > -1 and y > -1:
                self.centring_hwobj.appendCentringDataPoint(
                    {"X": (x - self.beam_position[0])/ self.pixels_per_mm_x,
                     "Y": (y - self.beam_position[1])/ self.pixels_per_mm_y})
            surface_score_list.append(score)
            self.phi_motor_hwobj.moveRelative(
                 360.0 / BESSY141Microdiff.AUTOMATIC_CENTRING_IMAGES)
            gevent.sleep(0.01)
            self.wait_device_ready(10)
        # self.omega_reference_add_constraint()
        centred_pos_dir = self.centring_hwobj.centeredPosition(return_by_name=False)
        #self.emit("newAutomaticCentringPoint", centred_pos_dir)

        return centred_pos_dir

    def motor_positions_to_screen(self, centred_positions_dict):
        """
        Descript. :
        """
        c = centred_positions_dict

        kappa = self.motor_hwobj_dict['kappa'].getPosition()
        phi = self.motor_hwobj_dict['kappa_phi'].getPosition()
        #IK TODO remove this director call

        if (c['kappa'], c['kappa_phi']) != (kappa, phi) \
         and self.minikappa_correction_hwobj is not None:
            #c['sampx'], c['sampy'], c['phiy']
            c['sampx'], c['sampy'], c['phiy'] = self.minikappa_correction_hwobj.shift(
            c['kappa'], c['kappa_phi'], [c['sampx'], c['sampy'], c['phiy']], kappa, phi)
        xy = self.centring_hwobj.centringToScreen(c)
        if xy:
            x = (xy['X'] + c['beam_x']) * self.pixels_per_mm_x + \
                 self.zoom_centre['x']
            y = (xy['Y'] + c['beam_y']) * self.pixels_per_mm_y + \
                 self.zoom_centre['y']
            return x, y
 
    def move_to_centred_position(self, centred_position):
        """
        Descript. :
        """
        GenericDiffractometer.move_to_centred_position(centred_position)

    def set_phase(self, phase, wait=False, timeout=None):
        if self.is_ready():
            self.cmd_start_set_phase(phase)
            if wait:
                if not timeout:
                    timeout = 40
                self.wait_device_ready(timeout)
        else:
            print "set_phase - Ready is: ", self.is_ready()

    def move_sync_motors(self, motors_dict, wait=True, timeout = 30):
        argin = ""
        logging.getLogger("HWR").debug("BESSY141Microdiff: in move_sync_motors, wait: %s, motors: %s, tims: %s " %(wait, motors_dict, time.time()))

        # 2017-09-18-bessy-mh: remove "pseudo-motors" beam_x, beam_y from dictionary
        #                      to be clarified why they are actually included here
        motors_dict_copy = motors_dict.copy()
        motors_dict_copy.pop("beam_x", None)
        motors_dict_copy.pop("beam_y", None)
        for motor in motors_dict_copy.keys():
            position = motors_dict[motor]
            if position is None:
                continue
            name=self.MOTOR_TO_EXPORTER_NAME[motor]
            argin += "%s=%0.3f," % (name, position)
        if not argin:
            return
        self.wait_device_ready(2000)
        self.cmd_move_sync_motors(argin)
	#task_info = self.command_dict["getTaskInfo"](task_id)
        if wait:
	    self.wait_device_ready(timeout)

    def get_centred_point_from_coord(self, x, y, return_by_names=None):
        """
        Descript. :
        """
        self.centring_hwobj.initCentringProcedure()
        self.centring_hwobj.appendCentringDataPoint({
                   "X" : (x - self.beam_position[0]) / self.pixels_per_mm_x,
                   "Y" : (y - self.beam_position[1]) / self.pixels_per_mm_y})
        # self.omega_reference_add_constraint()
        pos = self.centring_hwobj.centeredPosition()
        if return_by_names:
            pos = self.convert_from_obj_to_name(pos)
        return pos

    def convert_from_obj_to_name(self, motor_pos):
        motors = {}
        for motor_role in ('phiy', 'phiz', 'sampx', 'sampy', 'zoom',
                           'phi', 'focus', 'kappa', 'kappa_phi'):
            mot_obj = self.getObjectByRole(motor_role)
            try:
                motors[motor_role] = motor_pos[mot_obj]
            except KeyError:
                motors[motor_role] = mot_obj.getPosition()
        motors["beam_x"] = (self.beam_position[0] - \
                            self.zoom_centre['x'] )/self.pixels_per_mm_y
        motors["beam_y"] = (self.beam_position[1] - \
                            self.zoom_centre['y'] )/self.pixels_per_mm_x
        return motors

    def visual_align(self, point_1, point_2):
        """
        Descript. :
        """
        raise "NotImplementedException"

    def update_values(self):
        """
        Description:
        """
        self.emit('minidiffPhaseChanged', (self.current_phase, ))            
        # self.emit('omegaReferenceChanged', (self.reference_pos,))
        self.emit('minidiffShutterStateChanged', (self.fast_shutter_is_open, ))

    def toggle_fast_shutter(self):
        """
        Description:
        """
        if self.chan_fast_shutter_is_open is not None:
            self.chan_fast_shutter_is_open.setValue(not self.fast_shutter_is_open) 

    def find_loop(self):
        """
        Description:
        """
        image_array = self.camera_hwobj.get_snapshot(return_as_array=True)
        (info, x, y) = lucid.find_loop(image_array)
        surface_score = 10
        return x, y, surface_score

    def move_omega_relative(self, relative_angle):
        """
        Description:
        """
        self.phi_motor_hwobj.syncMoveRelative(relative_angle, 5)

    def close_kappa(self):
        """
        Descript. :
        """
        gevent.spawn(self.close_kappa_task) 

    def close_kappa_task(self):
        """Close kappa task
        """
        raise NotImplementedException

    def set_zoom(self, position): 
        """
        """
        self.zoom_motor_hwobj.moveToPosition(position)

    def zoom_in(self):
        self.zoom_motor_hwobj.zoom_in()

    def zoom_out(self):
        self.zoom_motor_hwobj.zoom_out()

    def get_point_from_line(self, point_one, point_two, frame_num, frame_total):
        """
        Descript. : method used to get a new motor position based on a position
                    between two positions. As arguments both motor positions are
                    given. frame_num and frame_total is used estimate new point position
                    Helical line goes from point_one to point_two.
                    In this direction also new position is estimated
        """
        raise NotImplementedException

    def get_osc_limits(self):
        return self.phi_motor_hwobj.getDynamicLimits()

    def get_osc_max_speed(self):
        return self.phi_motor_hwobj.getMaxSpeed()

    def get_scan_limits(self, speed=None, num_images=None, exp_time=None):
        """
        Gets scan limits. Necessary for example in the plate mode
        where osc range is limited
        """
        raise NotImplementedException

    def osc_scan(self, start, end, exptime, number_of_frames, wait=False):
        if self.in_plate_mode():
            scan_speed = math.fabs(end-start) / exptime
            low_lim, hi_lim = map(float, self.scanLimits(scan_speed))
            if start < low_lim:
                raise ValueError("Scan start below the allowed value %f" % low_lim)
            elif end > hi_lim:
                raise ValueError("Scan end abobe the allowed value %f" % hi_lim)

        scan_params = "1\t%0.3f\t%0.3f\t%0.4f\t1"% (start, (end-start), exptime)
        scan = self.addCommand({"type":"exporter", "exporter_address": self.exporter_addr, "name": "start_scan"}, "startScanEx")
        self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name": "number_of_frames" }, "ScanNumberOfFrames").setValue(number_of_frames)
        scan(scan_params)
        print "scan started at ----------->", time.time()
        if wait:
            self.wait_device_ready(300) #timeout of 5 min
            print "finished at ---------->", time.time()

    def osc_scan_4d(self, start, end, exptime, number_of_frames, motors_pos, wait=False):
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
        self.addChannel({ "type":"exporter", "exporter_address": self.exporter_addr, "name": "number_of_frames" }, "ScanNumberOfFrames").setValue(number_of_frames)
        scan(scan_params)
        print "scan started at ----------->", time.time()
        if wait:
            self.wait_device_ready(900) #timeout of 15 min
            print "finished at ---------->", time.time()

    def get_scintillator_position(self):
        return self.chan_scintillator_position.getValue()

    def set_scintillator_position(self, position):
        self.chan_scintillator_position.setValue(position)
        with gevent.Timeout(5, Exception("Timeout waiting for scintillator position")):
            while position != self.get_scintillator_position():
                gevent.sleep(0.01)

    def get_capillary_position(self):
        return self.chan_capillary_position.getValue()

    def set_capillary_position(self, position):
        self.chan_capillary_position.setValue(position)
        with gevent.Timeout(5, Exception("Timeout waiting for capillary position")):
            while position != self.get_capillary_position():
                gevent.sleep(0.01)

    def set_use_sc(self, flag):
        """Sets use_sc flag, that indicates if sample changer is used
        :param flag: use sample changer flag
        :type flag: boolean
        """
        if flag:
            self.use_sc = True
        else:
            self.use_sc = False

        return self.use_sc

    def cancel_centring_method_dummy(self):
        """Called when centring is aborted by user
        """
        pass
