#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
import logging
import gevent
import numpy as np

from PyQt4 import QtGui
from PyQt4 import QtCore

from Lima import Core 
from Lima import Prosilica


from HardwareRepository.BaseHardwareObjects import Device


class Qt4_LimaVideo(Device):
    """
    Descript. : 
    """
    def __init__(self, name):
        """
        Descript. :
        """
        Device.__init__(self, name)
        self.force_update = None
        self.cam_type = None
        self.cam_address = None
        self.cam_mirror = None
        self.cam_scale_factor = None
        
        self.brightness_exists = None 
        self.contrast_exists = None
        self.gain_exists = None
        self.gamma_exists = None

        self.qimage = None
        self.image_format = None
        self.image_dimensions = None

        self.camera = None
        self.interface = None
        self.control = None
        self.video = None 

        self.image_polling = None

    def init(self):
        """
        Descript. : 
        """
        self.force_update = False
        self.cam_type = self.getProperty("type").lower()
        self.cam_address = self.getProperty("address")

        try:       
            self.cam_mirror = eval(self.getProperty("mirror"))
        except:
            pass        

        if self.cam_type == 'prosilica':
            from Lima import Prosilica
            self.camera = Prosilica.Camera(self.cam_address)
            self.interface = Prosilica.Interface(self.camera)	

        self.control = Core.CtControl(self.interface)
        self.video = self.control.video()
        self.image_dimensions = list(self.camera.getMaxWidthHeight())
     
        self.setIsReady(True)

        if self.image_polling is None:
            self.video.startLive()
            self.change_owner()

            self.image_polling = gevent.spawn(self.do_image_polling,
                 self.getProperty("interval")/1000.0)

    def get_image_dimensions(self):
        return self.image_dimensions

    def get_scaling_factor(self):
        """
        Descript. :
        Returns   : Scaling factor in float. None if does not exists
        """ 
        return self.cam_scale_factor

    def imageType(self):
        """
        Descript. : returns image type
        """
        return self.image_format

    def start_camera(self):
        return 

    def setLive(self, mode):
        """
        Descript. :
        """
     
        return
        if mode:
            self.video.startLive()
            self.change_owner()
        else:
            self.video.stopLive()
    
    def change_owner(self):
        """
        Descript. :
        """
        if os.getuid() == 0:
            try:
                os.setgid(int(os.getenv("SUDO_GID")))
                os.setuid(int(os.getenv("SUDO_UID")))
            except:
                logging.getLogger().warning('%s: failed to change the process ownership.', self.name())
 
    def getWidth(self):
        """
        Descript. :
        """
        return int(self.image_dimensions[0])
	
    def getHeight(self):
        """
        Descript. :
        """
        return int(self.image_dimensions[1])

    def do_image_polling(self, sleep_time):
        """
        Descript. :
        """
        while self.video.getLive():
            self.get_new_image()
            time.sleep(sleep_time)
	     	
    def connectNotify(self, signal):
        """
        Descript. :
        """
        return
        """if signal == "imageReceived" and self.image_polling is None:
            self.image_polling = gevent.spawn(self.do_image_polling,
                 self.getProperty("interval")/1000.0)"""

    def refresh_video(self):
        """
        Descript. :
        """
        pass
 
    def get_new_image(self):
        """
        Descript. :
        """
        image = self.video.getLastImage()
        if image.frameNumber() > -1:
            raw_buffer = image.buffer()	
            qimage = QtGui.QImage(raw_buffer, image.width(), image.height(), 
                                  QtGui.QImage.Format_RGB888)
            if self.cam_mirror is not None:
                qimage = qimage.mirrored(self.cam_mirror[0], self.cam_mirror[1])     
            qpixmap = QtGui.QPixmap(qimage)
            self.emit("imageReceived", qpixmap)
            return qimage

    def save_snapshot(self, filename, image_type='PNG'):
        qimage = self.get_new_image() 
        qimage.save(filename, image_type) 

    def get_snapshot(self, bw=None, return_as_array=True):
        qimage = self.get_new_image()
        if return_as_array:
            qimage = qimage.convertToFormat(4)
            ptr = qimage.bits()
            ptr.setsize(qimage.byteCount())
            return np.array(ptr).reshape(qimage.height(), qimage.width(), 4)
            
        else:
            if bw:
                return qimage.convertToFormat(QtGui.QImage.Format_Mono)
            else:
                return qimage

    def get_contrast(self):
        return

    def set_contrast(self, contrast_value):
        return

    def get_brightness(self):
        return

    def set_brightness(self, brightness_value):
        return

    def get_gain(self):
        return

    def set_gain(self, gain_value):
        return

    def get_gamma(self):
        return

    def set_gamma(self, gamma_value):
        return

    def get_exposure_time(self):
        return

    def set_exposure_time(self, exposure_time_value):
        return
