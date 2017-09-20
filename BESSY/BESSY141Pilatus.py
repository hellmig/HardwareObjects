"""
[Name] BESSY141Pilatus

[Description]

[Properties]

[Referenced hardware objects]      
"""

import logging 
from AbstractDetector import AbstractDetector
from HardwareRepository.BaseHardwareObjects import HardwareObject

import BESSYLimaPilatus

class BESSY141Pilatus(AbstractDetector, HardwareObject):
    """
    Dummy description
    """

    def __init__(self, name): 
        """
        Descript. :
        """ 
        AbstractDetector.__init__(self)
        HardwareObject.__init__(self, name)

        # import detector distance hardware object
        self._detector_distance = None

        # set up real detector hardware object
        self._detector = BESSYLimaPilatus.Pilatus()

    def init(self):
        """
        Descript. :
        """
        self._detector_distance = self.getObjectByRole("detector_distance")

        self._detector.addCommand = self.addCommand
        self._detector.addChannel = self.addChannel
        self._detector.getCommandObject = self.getCommandObject
        self._detector.getChannelObject = self.getChannelObject

        # 2017-09-08-bessy-mh: configure internal LImA detector object
        config = {}
        config['lima_device'] = self.getProperty("lima_device")
        config['pilatus_device'] = self.getProperty("pilatus_device")
        config['create_remote_path_ssh'] = self.getProperty("create_remote_path_ssh")
        config['deadtime'] = self.getProperty("deadtime")
        config['minE'] = self.getProperty("minE")
        config['buffer'] = self.getProperty("buffer")
        config['serial'] = self.getProperty("serial")
        self._detector.init(config)

    def get_distance(self):
        if self._detector_distance:
            return self._detector_distance.getPosition()

    def get_distance_limits(self):
        if self._detector_distance:
            return self._detector_distance.getLimits()

    def has_shutterless(self):
        """Return True if has shutterless mode"""
        return self.getProperty("has_shutterless")

    def default_mode(self):
        return 1

    def get_detector_mode(self):
        return self.default_mode()

    def set_detector_mode(self, mode):
        return

    def get_minimum_exposure_time(self):
        """Returns minimum exposure time in [s]"""
        return self.getProperty("minimum_exposure_time")

    def get_image_file_suffix(self):
        """Returns the frame's filename extension"""
        return getProperty("file_suffix")

    def get_detector_type(self):
        """Returns the detector type string"""
        return getProperty("type")

    def get_detector_manufacturer(self):
        """Returns the detector manufacturer string"""
        return getProperty("manufacturer")

    def get_detector_model(self):
        """Returns the detector model string"""
        return getProperty("model")

    def get_pixel_size_x(self):
        """Returns the pixel size in X-direction [mm]"""
        return getProperty("px")

    def get_pixel_size_y(self):
        """Returns the pixel size in Y-direction [mm]"""
        return getProperty("py")

    def prepare_acquisition(
            self, take_dark, start, osc_range, exptime,
            npass, number_of_images, comment, energy, still, acq_params):
        """Configure aquisition parameters on the detector"""
        return self._detector.prepare_acquisition(
                   take_dark, start, osc_range, exptime, npass, number_of_images,
                   comment, energy, still, acq_params)

    def set_detector_filenames(
            self, frame_number, start, filename, jpeg_full_path, jpeg_thumbnail_full_path):
        """Configure file parameters on the detector"""
        return self._detector.set_detector_filenames(
                 frame_number, start, filename, jpeg_full_path, jpeg_thumbnail_full_path)

    def start_acquisition(self):
        return self._detector.start_acquisition()

    def get_deadtime(self):
        return self._detector.get_deadtime()

    def stop(self):
        return self._detector.stop()

