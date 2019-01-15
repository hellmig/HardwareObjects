"""
BESSY141DataCollectA hardware object

Derived from BIOMAXCollect.py, see also for documentation etc.
"""

import os
import logging
import gevent
import time
from HardwareRepository.TaskUtils import *
from HardwareRepository.BaseHardwareObjects import HardwareObject
from AbstractCollect import AbstractCollect


class BESSY141DataCollectA(AbstractCollect, HardwareObject):
    """
    Main data collection class. Inherited from AbstractCollect

    Collection is done by setting collection parameters and
    executing collect command
    """

    # 2017-09-12-bessy-mh: copied from Biomax implementation
    #                      not used yet, to be analysed
    # min images to trigger auto processing
    NIMAGES_TRIGGER_AUTO_PROC = 50

    def __init__(self, name):
        """
        Dummy description
        """
        AbstractCollect.__init__(self)
        HardwareObject.__init__(self, name)

        self._centring_status = None

        self.osc_id = None
        self.owner = None
        self._collecting = False
        self._error_msg = ""
        self._error_or_aborting = False
        self.collect_frame  = None
        self.helical = False
        self.helical_pos = None
        self.ready_event = None

        self.exp_type_dict = None

        self._notify_greenlet = None
        self.connect("collectImageTaken", self.collect_image_taken_handler)
        self.connect("collectOscillationFinished", self.collect_oscillation_finished_handler)

    def execute_command(self, command_name, *args, **kwargs):
        """
        Helper method to execute arbitrary external commands
        """
        wait = kwargs.get("wait", True)
        cmd_obj = self.getCommandObject(command_name)
        return cmd_obj(*args, wait = wait)

    def init(self):
        """
        Dummy description
        """
        self.ready_event = gevent.event.Event()
        self.diffractometer_hwobj = self.getObjectByRole("diffractometer")
        self.lims_client_hwobj = self.getObjectByRole("lims_client")
        self.machine_info_hwobj = self.getObjectByRole("machine_info")
        self.energy_hwobj = self.getObjectByRole("energy")
        self.resolution_hwobj = self.getObjectByRole("resolution")
        self.detector_hwobj = self.getObjectByRole("detector")
        self.autoprocessing_hwobj = self.getObjectByRole("auto_processing")
        self.beam_info_hwobj = self.getObjectByRole("beam_info")
        self.transmission_hwobj = self.getObjectByRole("transmission")
        self.detector_distance_hwobj = self.getObjectByRole("detector_distance")
        self.graphics_manager_hwobj = self.getObjectByRole("graphics_manager")

        self.chan_last_image_saved = self.addChannel({"type":"tango", "name": "last_image_saved", "polling":"events", "tangoname": "bl141/lima/camera"}, "last_image_saved")
        print self.chan_last_image_saved
        print self.chan_last_image_saved.getValue()
        self.connect(self.chan_last_image_saved, "update", self.last_image_updated)

        #todo
        self.detector_cover_hwobj = self.getObjectByRole("detector_cover") #use mockup now
        self.safety_shutter_hwobj = self.getObjectByRole("safety_shutter")
        self.fast_shutter_hwobj = self.getObjectByRole("fast_shutter")

        #todo
        #self.cryo_stream_hwobj = self.getObjectByRole("cryo_stream")

        undulators = []
        # todo
        try:
            for undulator in self["undulators"]:
                undulators.append(undulator)
        except:
            pass

        self.exp_type_dict = {'Mesh': 'Mesh','Helical': 'Helical'}
        self.set_beamline_configuration(\
             synchrotron_name = "BESSY",
             directory_prefix = self.getProperty("directory_prefix"),
             default_exposure_time = self.getProperty("default_exposure_time"),
             minimum_exposure_time = self.detector_hwobj.getProperty("minimum_exposure_time"),
             detector_fileext = self.detector_hwobj.getProperty("file_suffix"),
             detector_type = self.detector_hwobj.getProperty("type"),
             detector_manufacturer = self.detector_hwobj.getProperty("manufacturer"),
             detector_model = self.detector_hwobj.getProperty("model"),
             detector_px = self.detector_hwobj.getProperty("px"),
             detector_py = self.detector_hwobj.getProperty("py"),
             undulators = undulators,
             focusing_optic = self.getProperty('focusing_optic'),
             monochromator_type = self.getProperty('monochromator'),
             beam_divergence_vertical = self.beam_info_hwobj.get_beam_divergence_hor(),
             beam_divergence_horizontal = self.beam_info_hwobj.get_beam_divergence_ver(),
             polarisation = self.getProperty('polarisation'),
             input_files_server = self.getProperty("input_files_server"))

        """ to add """
        #self.chan_undulator_gap = self.getChannelObject('UndulatorGap')
        #self.chan_machine_current = self.getChannelObject("MachineCurrent")

        self.emit("collectConnected", (True,))
        self.emit("collectReady", (True, ))


    def do_collect(self, owner):
        """
        Actual collect sequence
        Note from BIOMAX staff: refactor do_collect!!!
        """

        log = logging.getLogger("user_level_log")
        log.info("Collection: Preparing to collect")
        # todo, add more exceptions and abort
        try:
            self.emit("collectReady", (False, ))
            self.emit("collectStarted", (owner, 1))

            # ----------------------------------------------------------------
            """ should all go data collection hook
            self.open_detector_cover()
            self.open_safety_shutter()
            self.open_fast_shutter()
            """

            # ----------------------------------------------------------------
            self.current_dc_parameters["status"] = "Running"
            self.current_dc_parameters["collection_start_time"] = \
                 time.strftime("%Y-%m-%d %H:%M:%S")
            self.current_dc_parameters["synchrotronMode"] = \
                 self.get_machine_fill_mode()

            log.info("Collection: Storing data collection in LIMS")
            self.store_data_collection_in_lims()

            log.info("Collection: Creating directories for raw images and processing files")
            self.create_file_directories()

            log.info("Collection: Getting sample info from parameters")
            self.get_sample_info()

            #log.info("Collect: Storing sample info in LIMS")
            #self.store_sample_info_in_lims()

            if all(item == None for item in self.current_dc_parameters['motors'].values()):
                # No centring point defined
                # create point based on the current position
                current_diffractometer_position = self.diffractometer_hwobj.getPositions()
                for motor in self.current_dc_parameters['motors'].keys():
                    self.current_dc_parameters['motors'][motor] = \
                         current_diffractometer_position[motor]

            log.info("Collection: Moving to centred position")
            #todo, self.move_to_centered_position() should go inside take_crystal_snapshots, 
            #which makes sure it move motors to the correct positions and move back 
            #if there is a phase change
            self.take_crystal_snapshots()

            # prepare beamline for data acquisiion
            self.prepare_acquisition()
            self.emit("collectOscillationStarted", \
                (owner, None, None, None, self.current_dc_parameters, None))

            self.data_collection_hook()
            self.emit_collection_finished()
        except:
            self.emit_collection_failed()
        # ----------------------------------------------------------------

        """ should all go data collection hook
        self.close_fast_shutter()
        self.close_safety_shutter()
        self.close_detector_cover()
        """

    def prepare_acquisition(self):
        """ todo
        1. check the currrent value is the same as the tobeset value
        2. check how to add detroi in the mode
        """
      
        log = logging.getLogger("user_level_log")
        if "transmission" in self.current_dc_parameters:
            log.info("Collection: Setting transmission to %.3f",
                     self.current_dc_parameters["transmission"])
            self.set_transmission(self.current_dc_parameters["transmission"])

        if "wavelength" in self.current_dc_parameters:
            log.info("Collection: Setting wavelength to %.3f", \
                     self.current_dc_parameters["wavelength"])
            self.set_wavelength(self.current_dc_parameters["wavelength"])
        elif "energy" in self.current_dc_parameters:
            log.info("Collection: Setting energy to %.3f",
                     self.current_dc_parameters["energy"])
            self.set_energy(self.current_dc_parameters["energy"])

        if "detroi" in self.current_dc_parameters:
            log.info("Collection: Setting detector to %s",
                     self.current_dc_parameters["detroi"])
            self.set_detector_roi(self.current_dc_parameters["detroi"])

        if "resolution" in self.current_dc_parameters:
            resolution = self.current_dc_parameters["resolution"]["upper"]
            log.info("Collection: Setting resolution to %.3f", resolution)
            self.set_resolution(resolution)

        elif 'detdistance' in self.current_dc_parameters:
            log.info("Collection: Moving detector to %f",
                     self.current_dc_parameters["detdistance"])
            self.move_detector(self.current_dc_parameters["detdistance"])

        log.info("Collection: Updating data collection in LIMS")
        self.update_data_collection_in_lims()
        self.prepare_detector()

        #move MD3 to DataCollection phase if it's not
        if self.diffractometer_hwobj.get_current_phase() != "DataCollection":
            log.info("Moving Diffractometer to Data Collection")
            self.diffractometer_hwobj.set_phase("DataCollection", wait=True, timeout=200)
        self.move_to_centered_position()


#-------------------------------------------------------------------------------


    def data_collection_hook(self):
        """
        Main collection command
        """
        parameters = self.current_dc_parameters

        log = logging.getLogger("user_level_info")
        log.info("data collection parameters received %s" % parameters)

        for parameter in parameters:
            log.info("%s: %s" % (str(parameter), str(parameters[parameter])))

        experiment_type = parameters["experiment_type"]

        if (experiment_type == "OSC") or (experiment_type == "Helical"):
            print "data_collection_hook: Standard shutterless data collection or Helical"

            try:
                oscillation_parameters = self.current_dc_parameters["oscillation_sequence"][0]

                # 2017-08-31-bessy-mh: migrate from BESSY141MultiCollect
                self.getChannelObject("parameters").setValue(oscillation_parameters)
                self.execute_command("build_collect_seq")
                self.execute_command("prepare_beamline")

                osc_start = oscillation_parameters['start']
                osc_end = osc_start + oscillation_parameters["range"] * \
                    oscillation_parameters['number_of_images']
                self.open_detector_cover()
                self.open_safety_shutter()
                #make sure detector configuration is finished
                # self._detector.wait_config_done()
                self.detector_hwobj.start_acquisition()
                # call after start_acquisition (detector is armed), when all the config parameters are definitely
                # implemented
                # shutterless_exptime = self._detector.get_acquisition_time()

                _exptime = oscillation_parameters['exposure_time']
                _number_of_images = oscillation_parameters['number_of_images']
                _detector_dead_time = self.detector_hwobj.get_deadtime()
                _shutterless_exptime = _number_of_images * (_exptime + _detector_dead_time)

                self.oscillation_task = self.oscil(osc_start, osc_end, _shutterless_exptime, 1, _number_of_images, wait=True)
                self.detector_hwobj.stop()

                self.close_safety_shutter()
                self.close_detector_cover()
                self.emit("collectImageTaken", oscillation_parameters['number_of_images'])
                # 2017-09-12-bessy-mh: call SPEC cleanup macro to finalize data collection
                self.execute_command("data_collection_cleanup")
            except:
                # 2017-09-12-bessy-mh: method data_collection_cleanup for ERROR cleanup only!
                #                      TO-DO: optimise naming
                self.data_collection_cleanup()
                raise Exception("data collection hook failed")
        elif experiment_type == "Characterization":
            print "data_collection_hook: Characterization"

            try:
                oscillation_parameters = self.current_dc_parameters["oscillation_sequence"][0]

                # 2017-08-31-bessy-mh: migrate from BESSY141MultiCollect
                self.getChannelObject("parameters").setValue(oscillation_parameters)

                self.execute_command("build_collect_seq")
                self.execute_command("prepare_beamline")

                self.open_detector_cover()
                self.open_safety_shutter()
                #make sure detector configuration is finished
                # self._detector.wait_config_done()
                self.detector_hwobj.start_acquisition()
                # call after start_acquisition (detector is armed), when all the config parameters are definitely
                # implemented
                # shutterless_exptime = self._detector.get_acquisition_time()

                _exptime = oscillation_parameters['exposure_time']
                _number_of_images = oscillation_parameters['number_of_images']
                _detector_dead_time = self.detector_hwobj.get_deadtime()
                _overlap = oscillation_parameters['overlap']
                _range = oscillation_parameters['range']

                for i in range(_number_of_images):
                    osc_start = oscillation_parameters['start'] + (_range - _overlap) * i
                    osc_end = osc_start + _range
                    self.oscillation_task = self.oscil(osc_start, osc_end, _exptime, 1, _number_of_images, wait=True)

                self.detector_hwobj.stop()

                self.close_safety_shutter()
                self.close_detector_cover()
                self.emit("collectImageTaken", oscillation_parameters['number_of_images'])
                # 2017-09-12-bessy-mh: call SPEC cleanup macro to finalize data collection
                self.execute_command("data_collection_cleanup")
            except:
                # 2017-09-12-bessy-mh: method data_collection_cleanup for ERROR cleanup only!
                #                      TO-DO: optimise naming
                self.data_collection_cleanup()
                raise Exception("data collection hook failed")
        else:
            print "data_collection_hook: Unknown data collection type"


    def oscil(self, start, end, exptime, npass, number_of_frames, wait = True):
        print "***** BESSY141DataCollectA.oscil: ", self.helical, start, end, exptime, npass, number_of_frames, wait
        if self.helical:
            self.diffractometer_hwobj.osc_scan_4d(start, end, exptime, number_of_frames, self.helical_pos, wait=True)
        else:
            self.diffractometer_hwobj.osc_scan(start, end, exptime, number_of_frames, wait=True)


    def emit_collection_failed(self):
        """
        Descrip. :
        """
        failed_msg = 'Data collection failed!'
        self.current_dc_parameters["status"] = failed_msg
        self.current_dc_parameters["comments"] = "%s\n%s" % (failed_msg, self._error_msg)
        self.emit("collectOscillationFailed", (self.owner, False,
             failed_msg, self.current_dc_parameters.get("collection_id"), self.osc_id))
        self.emit("collectEnded", self.owner, failed_msg)
        self.emit("collectReady", (True, ))
        self._collecting = None
        self.ready_event.set()

        self.update_data_collection_in_lims()

    def emit_collection_finished(self):
        """
        Dummy description
        """
        success_msg = "Data collection successful"
        self.current_dc_parameters["status"] = success_msg
        self.emit("collectOscillationFinished", (self.owner, True,
              success_msg, self.current_dc_parameters.get('collection_id'),
              self.osc_id, self.current_dc_parameters))
        self.emit("collectEnded", self.owner, success_msg)
        self.emit("collectReady", (True, ))
        self.emit("progressStop", ())
        self._collecting = None
        self.ready_event.set()

        self.update_data_collection_in_lims()

        last_frame = self.current_dc_parameters['oscillation_sequence'][0]['number_of_images']
        if last_frame > 1:
            self.store_image_in_lims_by_frame_num(last_frame)

        if (self.current_dc_parameters['experiment_type'] in ('OSC', 'Helical') and
            self.current_dc_parameters['oscillation_sequence'][0]['overlap'] == 0 and
            self.current_dc_parameters['oscillation_sequence'][0]['number_of_images'] >= \
                self.NIMAGES_TRIGGER_AUTO_PROC):
            self.trigger_auto_processing("after", self.current_dc_parameters, 0)

    def store_image_in_lims_by_frame_num(self, frame, motor_position_id=None):
        """
        Dummy description
        """
        pass

    def trigger_auto_processing(self, process_event, params_dict, frame_number):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.trigger_auto_processing", process_event, params_dict, frame_number
        # if self.autoprocessing_hwobj is not None:
        #     self.autoprocessing_hwobj.execute_autoprocessing(process_event,
        #                                                      self.current_dc_parameters,
        #                                                      frame_number)

    def open_detector_cover(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.open_detector_cover"
        pass
        # try:
        #     self.detector_cover_hwobj.set_out()
        # except:
        #     logging.getLogger("HWR").exception("Could not open the detector cover")
        #     pass

    def close_detector_cover(self):
        """
        Dummy description
        """
        pass

    def open_safety_shutter(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.open_safety_shutter"

    def close_safety_shutter(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.close_safety_shutter"

    def open_fast_shutter(self):
        """
        Not implemented, fast shutter synchronization handled by
        MD2 internfally
        """
        pass

    def close_fast_shutter(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.close_fast_shutter"
        self.execute_command("close_fast_shutter")

    @task
    def _take_crystal_snapshot(self, filename):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA._take_crystal_snapshot", filename
        self.graphics_manager_hwobj.save_scene_snapshot(filename)

    def set_detector_roi(self, value):
        """
        Set the detector roi mode
        """
        print "***** BESSY141DataCollectA.set_detector_roi", value
        # self.detector_hwobj.set_roi_mode(value)
        pass

    def set_helical(self, helical_on):
        """
        Dummy description
        """
        self.helical = helical_on

    def set_helical_pos(self, helical_oscil_pos):
        """
        Configure the helical data collection

        8 floats describe

        p1AlignmY, p1AlignmZ, p1CentrX, p1CentrY
        arg["1"]["phiy"], arg["1"]["phiz"], arg["1"]["sampx"], arg["1"]["sampy"]
        p2AlignmY, p2AlignmZ, p2CentrX, p2CentrY               
        arg["2"]["phiy"], arg["2"]["phiz"], arg["2"]["sampx"], arg["2"]["sampy"]
        """
        print "***** BESSY141DataCollectA.set_helical_pos", helical_oscil_pos
        self.helical_pos = helical_oscil_pos


    def set_resolution(self, value):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.set_resolution", value

        """ todo, move detector,
            but then should be done after set energy and roi
        """
        pass

    def set_energy(self, value):
        print "***** BESSY141DataCollectA.set_energy", value
        #todo,disabled temp
        #self.energy_hwobj.set_energy(value)
        #self.detector_hwobj.set_photon_energy(value*1000)

    def set_wavelength(self, value):
        print "***** BESSY141DataCollectA.set_wavelength", value
        #self.energy_hwobj.set_wavelength(value)
        #current_energy = self.energy_hwobj.get_energy()
        #self.detector_hwobj.set_photon_energy(value*1000)

    @task
    def move_motors(self, motor_position_dict):
        """
        Dummy description
        """
        self.diffractometer_hwobj.move_sync_motors(motor_position_dict)


    def create_file_directories(self):
        """
        Method create directories for raw files and processing files.
        Directorie for xds.input and auto_processing are created
        """
        self.create_directories(\
            self.current_dc_parameters['fileinfo']['directory'],
            self.current_dc_parameters['fileinfo']['process_directory'])

        """create processing directories and img links"""
        xds_directory,auto_directory = self.prepare_input_files()
        try:
            self.create_directories(xds_directory, auto_directory)
            #temporary, to improve
            os.system("chmod -R 777 %s %s" % (xds_directory, auto_directory))
            """todo, create link of imgs for auto_processing
            try:
                os.symlink(files_directory, os.path.join(process_directory, "img"))
            except os.error, e:
                if e.errno != errno.EEXIST:
                    raise
            """
            #os.symlink(files_directory, os.path.join(process_directory, "img"))
        except:
            logging.exception("Could not create processing file directory")
            return
        if xds_directory:
            self.current_dc_parameters["xds_dir"] = xds_directory
        if auto_directory:
            self.current_dc_parameters["auto_dir"] = auto_directory


    def prepare_input_files(self):
        """
        Dummy description
        """
        i = 1 
        logging.getLogger("user_level_log").info("Creating XDS (BESSY-BL141) processing input file directories")

        while True:
          xds_input_file_dirname = "xds_%s_%s_%d" % (\
              self.current_dc_parameters['fileinfo']['prefix'],
              self.current_dc_parameters['fileinfo']['run_number'],
              i)
          xds_directory = os.path.join(\
              self.current_dc_parameters['fileinfo']['directory'],
              "process", xds_input_file_dirname)
          if not os.path.exists(xds_directory):
            break
          i+=1
        auto_directory = os.path.join(\
              self.current_dc_parameters['fileinfo']['process_directory'],
              xds_input_file_dirname)
        return xds_directory, auto_directory

    def get_detector_distance(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_detector_distance"
        if self.detector_distance_hwobj is not None:
            return self.detector_distance_hwobj.getPosition()

    def get_detector_distance_limits(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_detector_distance_limits"
        #todo
        return 1000

    def prepare_detector(self):

        oscillation_parameters = self.current_dc_parameters["oscillation_sequence"][0]

        parameters = self.current_dc_parameters

        experiment_type = parameters["experiment_type"]

        _osc_range = oscillation_parameters["range"]
        if _osc_range < 1E-4:
            _still = True
        else:
            _still = False
        _take_dark = 0
        _energy = self.energy_hwobj.getCurrentEnergy()
        _omega_start = oscillation_parameters['start']
        _start_image_number = oscillation_parameters['start_image_number']
        _exptime = oscillation_parameters['exposure_time']
        _npass = 1
        _number_of_images = oscillation_parameters['number_of_images']
        _comment = "dummy"

        # insert here acq_params dictionary:
        _acq_params = {}
        _acq_params["kappa_phi"] = self.current_dc_parameters['motors'].get("kappa_phi", None)
        _acq_params["kappa"] = self.current_dc_parameters['motors'].get("kappa", None)
        _acq_params["polarisation"] = self.bl_config.polarisation
        _acq_params["transmission"] = self.get_transmission()
        _acq_params["flux"] = self.get_flux()
        _acq_params["beam_x"] = self.get_beam_centre()[0] / self.bl_config.detector_px
        _acq_params["beam_y"] = self.get_beam_centre()[1] / self.bl_config.detector_py
        # 2017-09-12-bessy-mh: CBF header expects detector distance in [m]
        _acq_params["detector_distance"] = self.get_detector_distance() / 1000.0
        _acq_params["wavelength"] = self.get_wavelength()

        # 2019-01-04-bessy-mh: overlap parameter for characterizations
        _acq_params["overlap"] = oscillation_parameters["overlap"]

        if (experiment_type == "OSC") or (experiment_type == "Helical"):
            print "prepare_detector: Standard/Helical shutterless data collection"
            # 2017-09-08-mh: customize to BESSY environment
            self.detector_hwobj.prepare_acquisition(
                _take_dark, _omega_start, _osc_range, _exptime, _npass, _number_of_images,
                _comment, _energy, _still, _acq_params)
        elif experiment_type == "Characterization":
            print "prepare_detector: Characterization"
            self.detector_hwobj.prepare_acquisition_single(
                _take_dark, _omega_start, _osc_range, _exptime, _npass, _number_of_images,
                _comment, _energy, _still, _acq_params)
        else:
           print "prepare_detector: Unknown data collection type"

        # Preparing directory path for images and processing files
        # creating image file template and jpegs files templates

        _file_parameters = self.current_dc_parameters["fileinfo"]
        _file_parameters["suffix"] = self.bl_config.detector_fileext
        _image_file_template = "%(prefix)s_%(run_number)s_%%04d.%(suffix)s" % _file_parameters
        _filename = _image_file_template % _start_image_number
        _file_location = _file_parameters["directory"]
        _file_path  = os.path.join(_file_location, _filename)
        _name_pattern = os.path.join(_file_parameters["directory"], _image_file_template)
        _file_parameters["template"] = _image_file_template
        _jpeg_full_path = None
        _jpeg_thumbnail_full_path = None

        self.detector_hwobj.set_detector_filenames(_start_image_number, _omega_start, str(_file_path), str(_jpeg_full_path), str(_jpeg_thumbnail_full_path))
        return

    def get_transmission(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_transmission"
        #todo
        return 100

    def set_transmission(self, value):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.set_transmission", value
        #todo
        if self.transmission_hwobj is not None:
            self.transmission_hwobj.setTransmission(value)

    def get_undulators_gaps(self):
        """
        Return triplet with gaps.
        """
        print "***** BESSY141DataCollectA.get_undulator_gaps"
        #todo
        return None, None, None

    def get_slit_gaps(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_slit_gaps"
        #todo
        return None, None

    def get_flux(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_flux"
        return self.get_measured_intensity()

    def collect_status_update(self, status):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.collect_status_update", status

    def collect_error_update(self, error_msg):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.collect_error_update", error_msg

    def update_lims_with_workflow(self, workflow_id, grid_snapshot_filename):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.update_lims_with_workflow", workflow_id, grid_snapshot_filename

    def collect_frame_update(self, frame):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.collect_frame_update", frame

    def getBeamlineConfiguration(self, *args):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.getBeamlineConfiguration"

    def get_measured_intensity(self):
        """
        Dummy description
        MAXIV implementation has method get_flux?!?
        """
        print "***** BESSY141DataCollectA.get_measured_intensity"
        return 1e99

    def setMeshScanParameters(self, num_lines, num_images_per_line, mesh_range):
        """
        Dummy description
        Copied from EMBL implementation. To be checked if really needed.
        """
        print "***** BESSY141DataCollectA.setMeshScanParameters", num_lines, num_images_per_line, mesh_range

    def data_collection_cleanup(self):
        # TO-DO: check if fast shutter is closed in macro
        self.execute_command("data_collection_cleanup")
        AbstractCollect.data_collection_cleanup(self)

    def adxv_notify(self, image_filename):
        logging.info("adxv_notify %r", image_filename)
        try:
            adxv_notify_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            adxv_notify_socket.connect(("hkl5.psf.bessy.de", 8100))
            adxv_notify_socket.sendall("load_image %s\n" % image_filename)
            adxv_notify_socket.close()
        except Exception, err:
            #logging.info("adxv_notify exception : %r", image_filename)
            #print Exception, err
            pass
#       else:
#           gevent.sleep(3)
        
    def collect_image_taken_handler(self, frame):
        print "***** BESSY141DataCollectA.collect_image_taken_handler", frame

    def collect_oscillation_finished_handler(self, owner, state, dc_status, collection_id, osc_id, data_collect_parameters):
        print "***** BESSY141DataCollectA.collect_oscillation_finished_handler", owner, state, dc_status, collection_id, osc_id, data_collect_parameters

    def get_machine_fill_mode(self):
        """
        Descript. : 
        """
        if self.machine_info_hwobj:
            fill_mode = str(self.machine_info_hwobj.get_fill_mode())
            return fill_mode
        else:
            return ''
    def get_archive_directory(self, directory):
        print "***** BESSY141DataCollectA.archive_directory", directory
        archive_dir = os.path.join(directory, "thumbnails")
        return archive_dir

    def directoryPrefix(self):
        print "***** BESSY141DataCollectA.directoryPrefix"
        dir = os.path.expandvars(self.bl_config.directory_prefix)
        return dir

    def get_cryo_temperature(self):
        """
        Dummy description
        """
        print "***** BESSY141DataCollectA.get_cryo_temperature"
        if self.cryo_hwobj is not None:
            return self.cryo_hwobj.getTemperature()
        else:
            return 999

    def get_beam_centre(self):
        """
        Descript. :
        """
        if self.detector_hwobj is not None:
            beam_x = self.detector_hwobj["beam"].getProperty("bx")
            beam_y = self.detector_hwobj["beam"].getProperty("by")
            return (beam_x, beam_y)
        else:
            return (None, None)

    def take_crystal_snapshots(self):
        """
        Descript. : 
        """
        log = logging.getLogger("user_level_log")
        print "***** BESSY141DataCollectA.take_crystal_snapshots"
        #move MD2 to DataCollection phase if it's not
        if self.diffractometer_hwobj.get_current_phase() != "Centring":
            log.info("Moving diffractometer to centring phase")
            self.diffractometer_hwobj.set_phase("Centring", wait=True, timeout=200)
        # 2017-09-12-bessy-mh: rewrite saving directory for the snapshots
        #                      TO-DO: introduce new configuration value
        #                      for aux data and/or Xtal snapshots
        save_dir = self.current_dc_parameters["fileinfo"]["archive_directory"]
        # use raw directory instead of archive path
        self.current_dc_parameters["fileinfo"]["archive_directory"] = \
            self.current_dc_parameters['fileinfo']['directory']
        AbstractCollect.take_crystal_snapshots(self)
        # switch back to standard archive directory
        self.current_dc_parameters["fileinfo"]["archive_directory"] = save_dir
        
    def last_image_updated(self, value):
        if value > 0:
            self.emit("collectImageTaken", int(value))

            _image_file_template = self.current_dc_parameters["fileinfo"]["template"]
            _filename = _image_file_template % int(value)
            _file_location = self.current_dc_parameters["fileinfo"]["directory"]
            _file_path  = os.path.join(_file_location, _filename)

            self.last_image_filename = _file_path

    def collectImageTakenHandler(self, frame):
        if self._notify_greenlet is None or self._notify_greenlet.ready():
            self._notify_greenlet = gevent.spawn_later(1, self.adxv_notify, self.last_image_filename)
