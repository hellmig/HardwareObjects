from BESSYMultiCollect import *
from detectors.LimaPilatus import Pilatus
import shutil
import logging
import gevent
import socket

class BESSY143MultiCollect(BESSYMultiCollect):
    def __init__(self, name):
        BESSYMultiCollect.__init__(self, name, PixelDetector(Pilatus), FixedEnergy(0.8950, 13.853))

        self._notify_greenlet = None
        self.connect("collectImageTaken", self.collectImageTakenHandler)
        self.connect("collectOscillationFinished", self.collectOscillationFinished_handler)


    @task
    def data_collection_cleanup(self):
      self.execute_command("data_collection_cleanup")
      #self.execute_command("close_fast_shutter")

       
    @task
    def data_collection_hook(self, data_collect_parameters):
      oscillation_parameters = data_collect_parameters["oscillation_sequence"][0]
     
      data_collect_parameters["dark"] = 0
      # are we doing shutterless ?
      #if oscillation_parameters["overlap"] != 0:
      #  shutterless = False
      #else:
      
      shutterless = data_collect_parameters.get("shutterless")
      self._detector.shutterless = True if shutterless else False
      #self.getChannelObject("shutterless").setValue(1 if shutterless else 0)

      self.getChannelObject("parameters").setValue(data_collect_parameters)
      self.execute_command("build_collect_seq")
      #self.execute_command("local_set_experiment_type")
      self.execute_command("prepare_beamline")

    @task
    def move_detector(self, detector_distance):
        self.bl_control.detector_distance.move(detector_distance)
        while self.bl_control.resolution.motorIsMoving():
           time.sleep(0.5)

    def get_detector_distance(self):
        return self.bl_control.detector_distance.getPosition()

    # New abstract methods in version 2.1
    #def set_detector_mode(self,mode):
    #    pass

    def generate_image_jpeg(self, filename, jpeg_path, jpeg_thumbnail_path, wait):
        pass 

    #def last_image_saved(self):
    #    if self._last_image_chan is not None:
    #        return self._last_image_chan.getValue()+1

    def set_helical(self,helical_on):
        pass

    def set_helical_pos(self,helical_pos):
        pass

    # end new abstract methods

    @task
    def set_resolution(self, new_resolution):
        self.bl_control.resolution.move(new_resolution)
        while self.bl_control.resolution.motorIsMoving():
           time.sleep(0.5)

    def get_beam_size(self):
        # should be moved to ESRFMultiCollect
        # (at the moment, ESRFMultiCollect is still using spec)
        return self.bl_control.beam_info.get_beam_size()

    def get_beam_shape(self):
        # should be moved to ESRFMultiCollect
        # (at the moment, ESRFMultiCollect is still using spec)
        return self.bl_control.beam_info.get_beam_shape()

    def get_resolution_at_corner(self):
        # should be moved to ESRFMultiCollect
        # (at the moment, ESRFMultiCollect is still using spec)
        return self.bl_control.resolution.get_value_at_corner()

    def get_beam_centre(self):
        # should be moved to ESRFMultiCollect
        # (at the moment, ESRFMultiCollect is still using spec)
        return self.bl_control.resolution.get_beam_centre()

    def trigger_auto_processing(self, process_event, *args, **kwargs):       
        if process_event in ('before', 'after'):
            return BESSYMultiCollect.trigger_auto_processing(self, process_event, *args, **kwargs)

    @task
    def write_input_files(self, datacollection_id):
        # copy *geo_corr.cbf* files to process directory
        try:
            process_dir = os.path.join(self.xds_directory, "..")
            raw_process_dir = os.path.join(self.raw_data_input_file_dir, "..") 
            for dir in (process_dir, raw_process_dir):
                for filename in ("x_geo_corr.cbf.bz2", "y_geo_corr.cbf.bz2"):
                    dest = os.path.join(dir,filename)
                    if os.path.exists(dest):
                        continue
                    shutil.copyfile(os.path.join("/data/id29/inhouse/opid291", filename), dest)
        except:
            logging.exception("Exception happened while copying geo_corr files")

        return BESSYMultiCollect.write_input_files(self, datacollection_id)

    @task
    def set_detector_filenames(self, frame_number, start, filename, jpeg_full_path, jpeg_thumbnail_full_path):
        # print "set_detector_filenames", frame_number, start, filename
        self.last_image_filename = filename
        return BESSYMultiCollect.set_detector_filenames(self, frame_number, start, filename, jpeg_full_path, jpeg_thumbnail_full_path)
        
    def adxv_notify(self, image_filename):
        logging.info("adxv_notify %r", image_filename)
        try:
            adxv_notify_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            adxv_notify_socket.connect(("hkl6.psf.bessy.de", 8100))
            adxv_notify_socket.sendall("load_image %s\n" % image_filename)
            adxv_notify_socket.close()
        except Exception, err:
            #logging.info("adxv_notify exception : %r", image_filename)
            #print Exception, err
            pass
#        else:
#            gevent.sleep(3)
        
    """
    def albula_notify(self, image_filename):
       try:
          albula_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
          albula_socket.connect(('hkl6.psf.bessy.de', 31337))
      except:
          pass
      else:
          albula_socket.sendall(pickle.dumps({ "type":"newimage", "path": image_filename }))
    """

    @task
    def write_image(self, last_frame):
        BESSYMultiCollect.write_image(self, last_frame)
#        if last_frame:
#            gevent.spawn_later(1, self.adxv_notify, self.last_image_filename)
#        else:
#            if self._notify_greenlet is None or self._notify_greenlet.ready():
#                self._notify_greenlet = gevent.spawn_later(1, self.adxv_notify, self.last_image_filename)

    def get_archive_directory(self, directory):
       
        archive_dir = os.path.join(directory, 'thumbnails')
        return archive_dir


    def trigger_auto_processing(self, process_event, xds_dir, EDNA_files_dir=None, 
                                anomalous=None, residues=200, inverse_beam=False, 
                                do_inducedraddam=False, in_multicollect=False, 
                                spacegroup=None, cell=None):
        pass


    def directoryPrefix(self):
        dir = os.path.expandvars(self.bl_config.directory_prefix)
        return dir


    def get_measured_intensity(self):
        return 1e11

    def collectImageTakenHandler(self, frame):
        if self._notify_greenlet is None or self._notify_greenlet.ready():
            self._notify_greenlet = gevent.spawn_later(1, self.adxv_notify, self.last_image_filename)

    def collectOscillationFinished_handler(self, owner, state, dc_status, collection_id, osc_id, data_collect_parameters):
        if self._notify_greenlet is None or self._notify_greenlet.ready():
            self._notify_greenlet = gevent.spawn_later(1, self.adxv_notify, self.last_image_filename)

