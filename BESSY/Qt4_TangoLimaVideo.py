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

"""
[Name]
Qt4_TangoLimaVideo

[Description]
HwObj used to grab images via Tango Lima device server
If you want to access the Lima Library directly you may consider using
the Qt4_LimaVideo module instead

[Configuration]
Example Hardware Object XML file :
==================================
<device class="Qt4_LimaVideo">
   <type>basler</type>
   <encoding>yuv422p</encoding>
   <tangoname>bl13/eh/lima_oav</tangoname>
   <gain>0.5</gain>
   <exposure>0.01</exposure>
   <mirror>(False, False)</mirror>
   <interval>30</interval>
</device>
"""

import os
import time
import logging
import struct
import numpy as np

import PyTango

from GenericVideoDevice import GenericVideoDevice

class Qt4_TangoLimaVideo(GenericVideoDevice):
    """
    Descript. : 
    """
    def __init__(self, name):
        """
        Descript. :
        """
        GenericVideoDevice.__init__(self, name)
        self.device = None

    def init(self):
        """
        Descript. : 
        """

        tangoname = self.getProperty("tangoname")

        self.device = PyTango.DeviceProxy(tangoname)
        self.device.ping()

        GenericVideoDevice.init(self)

    def set_cam_encoding(self, cam_encoding):
        if cam_encoding == "yuv422p":
            self.device.video_mode = "YUV422"
        elif cam_encoding == "y8":
            self.device.video_mode = "Y8"
        elif cam_encoding == "rgb24":
            self.device.video_mode = "RGB24"
  
        GenericVideoDevice.set_cam_encoding(self, cam_encoding)

    """ Overloading of GenericVideoDevice methods """
    def get_image_dimensions(self):
        return [self.device.image_width, self.device.image_height]

    def get_image(self):
        img_data = self.device.video_last_image

        if img_data[0]=="VIDEO_IMAGE":
            header_fmt = ">IHHqiiHHHH"
            _, ver, img_mode, frame_number, width, height, _, _, _, _ = struct.unpack(header_fmt, img_data[1][:struct.calcsize(header_fmt)])
            if self.device.video_mode == "RGB24":
                raw_buffer = img_data[1][32:]
            else:
                raw_buffer = np.fromstring(img_data[1][32:], np.uint16)
        return raw_buffer, width, height

    def get_gain(self):
        if self.get_cam_type() in ("basler", "prosilica"):
            value = self.device.video_gain
            return value

    def set_gain(self, gain_value):
        if self.get_cam_type() in ("basler", "prosilica"):
            self.device.video_gain = gain_value
            return

    def get_exposure_time(self):
        if self.get_cam_type() in ("basler", "prosilica"):
            return self.device.video_exposure

    def set_exposure_time(self, exposure_time_value):
        if self.get_cam_type() in ("basler", "prosilica"):
            self.device.video_exposure = exposure_time_value
        
    def get_video_live(self):
        return self.device.video_live 

    def set_video_live(self, flag):
        self.device.video_live = flag

    """ END Overloading of GenericVideoDevice methods """


def test_hwo(hwo):
    print "Image dimensions: ", hwo.get_image_dimensions()
    print "Live Mode: ", hwo.get_video_live()

