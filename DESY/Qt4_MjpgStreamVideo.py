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
#   You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.


__author__ = "Jan Meyer"
__email__ = "jan.meyer@desy.de"
__copyright__ = "(c)2015 DESY, FS-PE, P11"
__license__ = "GPL"


import gevent
import httplib
import json

from PyQt4 import QtGui
from PyQt4 import QtCore

from HardwareRepository.BaseHardwareObjects import Device


class Qt4_MjpgStreamVideo(Device):
    """
    Hardware object to capture images using mjpg-streamer
    and it's input_avt.so plugin for AVT Prosilica cameras.
    """

    # command / control types supported by mjpg-streamer
    CTRL_TYPE_INTEGER = 1
    CTRL_TYPE_BOOLEAN = 2
    CTRL_TYPE_MENU = 3
    CTRL_TYPE_BUTTON = 4

    # command destinations
    DEST_INPUT = 0
    DEST_OUTPUT = 1
    DEST_PROGRAM = 2

    # command groups
    IN_CMD_GROUP_GENERIC = 0
    IN_CMD_GROUP_RESOLUTION = 2
    IN_CMD_GROUP_JPEG_QUALITY = 3
    IN_CMD_GROUP_AVT_MISC = 32
    IN_CMD_GROUP_AVT_INFO = 33
    IN_CMD_GROUP_AVT_EXPOSURE = 34
    IN_CMD_GROUP_AVT_GAIN = 35
    IN_CMD_GROUP_AVT_LENS_DRIVE = 36
    IN_CMD_GROUP_AVT_IRIS = 37
    IN_CMD_GROUP_AVT_WHITE_BALANCE = 38
    IN_CMD_GROUP_AVT_DSP = 39
    IN_CMD_GROUP_AVT_IMAGE_FORMAT = 40
    IN_CMD_GROUP_AVT_IO = 41
    IN_CMD_GROUP_AVT_ACQUISITION = 42
    IN_CMD_GROUP_AVT_CONFIG_FILE = 43
    IN_CMD_GROUP_AVT_NETWORK = 44
    IN_CMD_GROUP_AVT_STATS = 45
    IN_CMD_GROUP_AVT_EVENTS = 46

    # commands
    # note: not every camera supports every command
    # mjpg-streamer only supports integer values for commands
    #   float values are therefore submitted as an integer value * 1000
    #   booleans will only accept 0 or 1
    #   menus have an integer identifier for every item
    #   commands will ignore the given value
    #   strings and events are unsupported yet
    # for more information see the "AVT Camera and Driver Attributes" manual
    IN_CMD_UPDATE_CONTROLS = (1, IN_CMD_GROUP_GENERIC)
    IN_CMD_JPEG_QUALITY = (1, IN_CMD_GROUP_JPEG_QUALITY)
    IN_CMD_AVT_ACQ_END_TRIGGER_EVENT = (6, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQ_END_TRIGGER_MODE = (7, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQ_REC_TRIGGER_EVENT = (8, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQ_REC_TRIGGER_MODE = (9, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQ_START_TRIGGER_EVENT = (10, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQ_START_TRIGGER_MODE = (11, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQUISITION_ABORT = (5, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQUISITION_FRAME_COUNT = (2, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQUISITION_MODE = (1, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQUISITION_START = (3, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_ACQUISITION_STOP = (4, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_BANDWIDTH_CTRL_MODE = (1, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_BINNING_X = (1, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    IN_CMD_AVT_BINNING_Y = (2, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    # String 2 IN_CMD_AVT_CAMERA_NAME = (0, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_CHUNK_MODE_ACTIVE = (2, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_CONFIG_FILE_INDEX = (1, IN_CMD_GROUP_AVT_CONFIG_FILE)
    IN_CMD_AVT_CONFIG_FILE_LOAD = (3, IN_CMD_GROUP_AVT_CONFIG_FILE)
    IN_CMD_AVT_CONFIG_FILE_POWER_UP = (2, IN_CMD_GROUP_AVT_CONFIG_FILE)
    IN_CMD_AVT_CONFIG_FILE_SAVE = (4, IN_CMD_GROUP_AVT_CONFIG_FILE)
    IN_CMD_AVT_DSP_SUBREGION_BOTTOM = (4, IN_CMD_GROUP_AVT_DSP)
    IN_CMD_AVT_DSP_SUBREGION_LEFT = (1, IN_CMD_GROUP_AVT_DSP)
    IN_CMD_AVT_DSP_SUBREGION_RIGHT = (3, IN_CMD_GROUP_AVT_DSP)
    IN_CMD_AVT_DSP_SUBREGION_TOP = (2, IN_CMD_GROUP_AVT_DSP)
    IN_CMD_AVT_DEFECT_MASK_COLUMN_ENABLE = (1, IN_CMD_GROUP_AVT_MISC)
    # String 14 IN_CMD_AVT_DEVICE_ETH_ADDRESS = (0, IN_CMD_GROUP_AVT_NETWORK)
    # String 3 IN_CMD_AVT_DEVICE_FIRMWARE_VERSION = (0, IN_CMD_GROUP_AVT_INFO)
    # String 15 IN_CMD_AVT_DEVICE_IP_ADDRESS = (0, IN_CMD_GROUP_AVT_NETWORK)
    # String 4 IN_CMD_AVT_DEVICE_MODEL_NAME = (0, IN_CMD_GROUP_AVT_INFO)
    # String 5 IN_CMD_AVT_DEVICE_PART_NUMBER = (0, IN_CMD_GROUP_AVT_INFO)
    # String 6 IN_CMD_AVT_DEVICE_SCAN_TYPE = (0, IN_CMD_GROUP_AVT_INFO)
    # String 7 IN_CMD_AVT_DEVICE_SERIAL_NUMBER = (0, IN_CMD_GROUP_AVT_INFO)
    # String 8 IN_CMD_AVT_DEVICE_VENDOR_NAME = (0, IN_CMD_GROUP_AVT_INFO)
    # Event IN_CMD_AVT_EVENT_ACQUISITION_END = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_ACQUISITION_RECORD_TRIGGER = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_ACQUISITION_START = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_ERROR = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_EXPOSURE_END = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_FRAME_TRIGGER = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_NOTIFICATION = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_OVERFLOW = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SELECTOR = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN1_FALL = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN1_RISE = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN2_FALL = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN2_RISE = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN3_FALL = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN3_RISE = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN4_FALL = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENT_SYNC_IN4_RISE = (0, IN_CMD_GROUP_AVT_EVENTS)
    # Event IN_CMD_AVT_EVENTS_ENABLE1 = (0, IN_CMD_GROUP_AVT_EVENTS)
    IN_CMD_AVT_EXPOSURE_AUTO_ADJUST_TOL = (3, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_ALG = (4, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_MAX = (5, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_MIN = (6, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_OUTLIERS = (7, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_RATE = (8, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_AUTO_TARGET = (9, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_MODE = (2, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_EXPOSURE_VALUE = (1, IN_CMD_GROUP_AVT_EXPOSURE)
    IN_CMD_AVT_FIRMWARE_VER_BUILD = (9, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_FIRMWARE_VER_MAJOR = (10, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_FIRMWARE_VER_MINOR = (11, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_FRAMERATE = (12, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_FRAME_START_TRIGGER_DELAY = (14, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_FRAME_START_TRIGGER_EVENT = (15, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_FRAME_START_TRIGGER_MODE = (13, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_FRAME_START_TRIGGER_OVERLAP = (16, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_FRAME_START_TRIGGER_SOFTWARE = (17, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_GAIN_AUTO_ADJUST_TOL = (3, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_AUTO_MAX = (4, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_AUTO_MIN = (5, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_AUTO_OUTLIERS = (6, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_AUTO_RATE = (7, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_AUTO_TARGET = (8, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_MODE = (2, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GAIN_VALUE = (1, IN_CMD_GROUP_AVT_GAIN)
    IN_CMD_AVT_GVSP_LOOKBACK_WINDOW = (18, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_GVSP_RESEND_PERCENT = (19, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_GVSP_RETRIES = (20, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_GVSP_SOCKET_BUFFERS_COUNT = (21, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_GVSP_TIMEOUT = (22, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_HEARTBEAT_INTERVAL = (23, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_HEARTBEAT_TIMEOUT = (24, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_HEIGHT = (6, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    # String 16 IN_CMD_AVT_HOST_ETH_ADDRESS = (0, IN_CMD_GROUP_AVT_NETWORK)
    # String 17 IN_CMD_AVT_HOST_IP_ADDRESS = (0, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_IRIS_AUTOTARGET = (1, IN_CMD_GROUP_AVT_IRIS)
    IN_CMD_AVT_IRIS_MODE = (2, IN_CMD_GROUP_AVT_IRIS)
    IN_CMD_AVT_IRIS_VIDEO_LEVEL = (3, IN_CMD_GROUP_AVT_IRIS)
    IN_CMD_AVT_IRIS_VIDEO_LEVEL_MAX = (4, IN_CMD_GROUP_AVT_IRIS)
    IN_CMD_AVT_IRIS_VIDEO_LEVEL_MIN = (5, IN_CMD_GROUP_AVT_IRIS)
    IN_CMD_AVT_LENS_DRIVE_COMMAND = (1, IN_CMD_GROUP_AVT_LENS_DRIVE)
    IN_CMD_AVT_LENS_DRIVE_DURATION = (2, IN_CMD_GROUP_AVT_LENS_DRIVE)
    IN_CMD_AVT_LENS_VOLTAGE = (3, IN_CMD_GROUP_AVT_LENS_DRIVE)
    IN_CMD_AVT_LENS_VOLTAGE_CONTROL = (4, IN_CMD_GROUP_AVT_LENS_DRIVE)
    IN_CMD_AVT_MULTICAST_ENABLE = (25, IN_CMD_GROUP_AVT_NETWORK)
    # String 26 IN_CMD_AVT_MULTICAST_IP_ADDRESS = (0, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_NON_IMAGE_PAYLOAD_SIZE = (3, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_PACKET_SIZE = (27, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_PART_CLASS = (12, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_PART_NUMBER = (13, IN_CMD_GROUP_AVT_INFO)
    # String 14 IN_CMD_AVT_PART_REVISION = (0, IN_CMD_GROUP_AVT_INFO)
    # String 15 IN_CMD_AVT_PART_VERSION = (0, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_PAYLOAD_SIZE = (4, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_PIXEL_FORMAT = (7, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    IN_CMD_AVT_RECORDER_PRE_EVENT_COUNT = (18, IN_CMD_GROUP_AVT_ACQUISITION)
    IN_CMD_AVT_REGION_X = (3, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    IN_CMD_AVT_REGION_Y = (4, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    IN_CMD_AVT_SENSOR_BITS = (20, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_SENSOR_HEIGHT = (18, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_SENSOR_TYPE = (19, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_SENSOR_WIDTH = (17, IN_CMD_GROUP_AVT_INFO)
    # String 16 IN_CMD_AVT_SERIAL_NUMBER = (0, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_STAT_DRIVER_TYPE = (1, IN_CMD_GROUP_AVT_STATS)
    # String 2 IN_CMD_AVT_STAT_FILTER_VERSION = (0, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_FRAME_RATE = (3, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_FRAMES_COMPLETED = (4, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_FRAMES_DROPPED = (5, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_PACKETS_ERRONEOUS = (6, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_PACKETS_MISSED = (7, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_PACKETS_RECEIVED = (8, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_PACKETS_REQUESTED = (9, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STAT_PACKETS_RESENT = (10, IN_CMD_GROUP_AVT_STATS)
    IN_CMD_AVT_STREAM_BYTES_PER_SECOND = (6, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_STREAM_FRAME_RATE_CONSTRAIN = (5, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_STREAM_HOLD_CAPACITY = (8, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_STREAM_HOLD_ENABLE = (7, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_STROBE1_CONTROLLED_DURATION = (1, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_STROBE1_DELAY = (3, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_STROBE1_DURATION = (4, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_STROBE1_MODE = (2, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_IN1_GLITCH_FILTER = (5, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_IN2_GLITCH_FILTER = (6, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_IN_LEVELS = (7, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT1_INVERT = (9, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT1_MODE = (10, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT2_INVERT = (11, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT2_MODE = (12, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT3_INVERT = (13, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT3_MODE = (14, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT4_INVERT = (15, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT4_MODE = (16, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_SYNC_OUT_GPO_LEVELS = (8, IN_CMD_GROUP_AVT_IO)
    IN_CMD_AVT_TIME_STAMP_FREQUENCY = (9, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_TIME_STAMP_RESET = (13, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_TIME_STAMP_VALUE_HI = (11, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_TIME_STAMP_VALUE_LATCH = (12, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_TIME_STAMP_VALUE_LO = (10, IN_CMD_GROUP_AVT_NETWORK)
    IN_CMD_AVT_TOTAL_BYTES_PER_FRAME = (8, IN_CMD_GROUP_AVT_IMAGE_FORMAT)
    IN_CMD_AVT_UNIQUE_ID = (1, IN_CMD_GROUP_AVT_INFO)
    IN_CMD_AVT_VSUB_VALUE = (2, IN_CMD_GROUP_AVT_MISC)
    IN_CMD_AVT_WHITEBAL_AUTO_ADJUST_TOL = (4, IN_CMD_GROUP_AVT_WHITE_BALANCE)
    IN_CMD_AVT_WHITEBAL_AUTO_RATE = (5, IN_CMD_GROUP_AVT_WHITE_BALANCE)
    IN_CMD_AVT_WHITEBAL_MODE = (3, IN_CMD_GROUP_AVT_WHITE_BALANCE)
    IN_CMD_AVT_WHITEBAL_VALUE_BLUE = (2, IN_CMD_GROUP_AVT_WHITE_BALANCE)
    IN_CMD_AVT_WHITEBAL_VALUE_RED = (1, IN_CMD_GROUP_AVT_WHITE_BALANCE)
    IN_CMD_AVT_WIDTH = (5, IN_CMD_GROUP_AVT_IMAGE_FORMAT)


    def __init__(self, name):
        """
        Descript. :
        """
        Device.__init__(self, name)
        self.force_update = None
        self.image_dimensions = None
        self.image_polling = None
        self.image_type = None
        self.image = None
        self.sleep_time = 1
        self.flip = {"h": False, "v": False}
        self.host = None
        self.port = None
        self.path = "/"
        self.plugin = 0
        self.updateControls = None
        self.inputAvt = None

    def init(self):
        """
        Descript. :
        """ 
        self.sleep_time = self.getProperty("interval")
        width = self.getProperty("width")
        height = self.getProperty("height")
        self.image_dimensions = (width, height)
        self.flip["h"] = bool(self.getProperty("fliph"))
        self.flip["v"] = bool(self.getProperty("flipv"))
        self.host = self.getProperty("host")
        self.port = int(self.getProperty("port"))
        self.path = "/"
        self.plugin = 0
        self.updateControls = self.hasUpdateControls()
        self.inputAvt = self.isInputAvt()
        self.image = self.get_new_image()
        self.setIsReady(True)

    def httpGet(self, query, host=None, port=None, path=None):
        """Sends HTTP GET requests and returns the answer.
        
        Keyword arguments:
        query -- string appended to the end of the requested URL
        host -- queried IP or hostname (default host of the MjpgStream instance)
        port -- queried port number (default port of the MjpgStream instance)
        path -- queried path (default path of the MjpgStream instance)
        
        Return value:
        the HTTP answer content or None on error
        
        """
        if(host is None): host = self.host
        if(port is None): port = self.port
        if(path is None): path = self.path
        # send get request and return response
        http = httplib.HTTPConnection(host, port, timeout=3)
        try:
            http.request("GET", path+query)
            response = http.getresponse()
        except:
            logging.getLogger().error("MjpgStreamVideo: Connection to http://{0}:{1}{2}{3} refused".format(host, port, path, query))
            return None
        if response.status != 200:
            logging.getLogger().error("MjpgStreamVideo: Error {0}, {1}".format(response.status, response.reason))
            return None
        data = response.read()
        http.close()
        return data

    def sendCmd(self, value, cmd, group=None, plugin=None, dest=None):
        """Sends a command to mjpg-streamer.
        
        Keyword arguments:
        value -- command parameter as integer or item name as string if the command is of enumeration type
        cmd -- command id number or tuple constant
        group -- command group number, leave it at None if a tuple is given as cmd (default None)
        plugin -- plugin number (default plugin of the MjpgStream instance)
        dest -- command destination  (default MjpgStream.DEST_INPUT)
        
        """
        if(isinstance(cmd, tuple) and group is None):
            group = cmd[1]
            cmd = cmd[0]
        elif(isinstance(cmd, tuple)):
            cmd = cmd[0]
        if(group is None):
            return None
        cmd = str(int(cmd))
        group = str(int(group))
        try:
            value = str(int(value))
        except:
            option = value
            value = None
            if(type(option) is str):
                info = self.getCmdInfo(cmd, group)
                if(info and "menu" in info and option in info["menu"].values()):
                    value = str([k for k, v in info["menu"].iteritems() if(v == option)][0])
            if(value is None):
                return None
        if(plugin is None):
            plugin = str(self.plugin)
        else:
            plugin = str(int(plugin))
        if(dest is None):
            dest = str(self.DEST_INPUT)
        else:
            dest = str(int(dest))
        # send request
        self.httpGet("?action=command&id="+cmd+"&dest="+dest+"&group="+group+"&value="+value+"&plugin="+plugin)

    def hasCmd(self, cmd, group=None, plugin=None, dest=None):
        """Checks whether a command with the given id and group is known by the specified plugin.
        
        Keyword arguments:
        cmd -- command id number or tuple constant
        group -- command group number, leave it at None if a tuple is given as cmd (default None)
        plugin -- plugin number (default plugin of the MjpgStream instance)
        dest -- command destination  (default MjpgStream.DEST_INPUT)
        
        Return value:
        True if so, False if not or the connection was refused
        
        """
        data = self.getCmdInfo(cmd, group, plugin, dest)
        if(not data is None):
            return True
        return False

    def getCmdInfo(self, cmd, group=None, plugin=None, dest=None):
        """Returns a dictionary with informations on the queried command.
        
        Keyword arguments:
        cmd -- command id number or tuple constant
        group -- command group number, leave it at None if a tuple is given as cmd (default None)
        plugin -- plugin number (default plugin of the MjpgStream instance)
        dest -- command destination  (default MjpgStream.DEST_INPUT)
        
        Return value:
        dictionary containing the following items ("menu" only for menu commands): 
        "name", "id", "type", "min", "max", "step", "default", "value", "dest", "flags", "group", "menu"
        or None on error
        
        """
        if(isinstance(cmd, tuple) and group is None):
            group = cmd[1]
            cmd = cmd[0]
        elif(isinstance(cmd, tuple)):
            cmd = cmd[0]
        if(group is None):
            return None
        if(plugin is None):
            plugin = self.plugin
        else:
            plugin = str(int(plugin))
        if(dest is None or (dest != self.DEST_INPUT and dest != self.DEST_OUTPUT)):
            dest = self.DEST_INPUT
        if(self.updateControls):
            self.sendCmd(group, self.IN_CMD_UPDATE_CONTROLS, plugin, dest)
        # get list of controls and search for the matching one
        data = self.getControls(plugin, dest)
        if(data != None):
            for info in data:
                if(int(info["group"]) == int(group) and int(info["id"]) == int(cmd)):
                    return info
        return None

    def getControls(self, plugin=None, dest=None):
        """Returns a list with information on all commands supported by the 
        plugin. If DEST_PROGRAM is given for dest, a list with information on 
        all loaded plugins is returned.
        
        Keyword arguments:
        plugin -- plugin number (default plugin of the MjpgStream instance)
        dest -- command destination  (default MjpgStream.DEST_INPUT)
        
        Return value:
        depends on destination plugin. For input_avt.so a list with all commands 
        supported by the connected camera is returned - q.v. getCmdInfo().
        
        """
        if(plugin is None):
            plugin = str(self.plugin)
        else:
            plugin = str(int(plugin))
        if(dest is None):
            dest = self.DEST_INPUT
        else:
            dest = int(dest)
        query = None
        if(dest == self.DEST_INPUT):
            query = "input_"+plugin+".json"
        elif(dest == self.DEST_OUTPUT):
            query = "output_"+plugin+".json"
        elif(dest == self.DEST_PROGRAM):
            query = "program.json"
        # fetch json from server, decode it into a python object and return it
        if(query is not None):
            data = self.httpGet(query)
            if(data is not None):
                data = json.loads(data)
                if(dest != self.DEST_PROGRAM and "controls" in data):
                    data = data["controls"]
                return data
        return None

    def hasUpdateControls(self):
        """Checks if the default plugin for this instance knows the UpdateControls command.
        
        Return value:
        True if so, False if not and None if the connection was refused
        
        """
        data = self.getCmdInfo(self.IN_CMD_UPDATE_CONTROLS)
        if(data is None):
            return None
        if(data["name"] == "UpdateControls"):
            return True
        return False

    def isInputAvt(self):
        """Checks if the default plugin for this instance is input_avt.so.
        
        Return value:
        True if so, False if not and None if the connection was refused
        
        """
        data = self.getControls(0, self.DEST_PROGRAM)
        if(data is None):
            return None
        if(data.has_key("inputs")):
            for info in data["inputs"]:
                if(info["name"][:12] == "input_avt.so"):
                    return True
        return False

    def start_camera(self):
        if self.image_polling is None:
            self.image_polling = gevent.spawn(self._do_imagePolling, 1.0 / self.sleep_time)

    def get_image_dimensions(self):
        return self.image_dimensions

    def imageType(self):
        """
        Descript. :
        """
        return

    def contrastExists(self):
        """
        Descript. :
        """
        return

    def setContrast(self, contrast):
        """
        Descript. :
        """
        return

    def getContrast(self):
        """
        Descript. :
        """
        return 

    def getContrastMinMax(self):
        """
        Descript. :
        """
        return 

    def brightnessExists(self):
        """
        Descript. :
        """
        return

    def setBrightness(self, brightness):
        """
        Descript. :
        """
        return

    def getBrightness(self):
        """
        Descript. :
        """ 
        return 

    def getBrightnessMinMax(self):
        """
        Descript. :
        """
        return 

    def gainExists(self):
        """
        Descript. :
        """
        return self.hasCmd(self.IN_CMD_AVT_GAIN_VALUE)

    def setGain(self, gain):
        """
        Descript. :
        """
        self.sendCmd("Manual", self.IN_CMD_AVT_GAIN_MODE) # gain mode manual
        self.sendCmd(gain, self.IN_CMD_AVT_GAIN_VALUE)

    def getGain(self):
        """
        Descript. :
        """
        info = self.getCmdInfo(self.IN_CMD_AVT_GAIN_VALUE)
        if info is not None:
            return info["value"]
        return

    def getGainMinMax(self):
        """
        Descript. :
        """
        info = self.getCmdInfo(self.IN_CMD_AVT_GAIN_VALUE)
        if info is not None:
            value = (info["min"], info["max"])
        return 

    def gammaExists(self):
        """
        Descript. :
        """
        return

    def setGamma(self, gamma):
        """
        Descript. :
        """
        return

    def getGamma(self):
        """
        Descript. :
        """
        return 

    def getGammaMinMax(self):
        """
        Descript. :
        """ 
        return (0, 1)

    def setLive(self, mode):
        """
        Descript. :
        """
        return
    
    def getWidth(self):
        """
        Descript. :
        """
        return self.image_dimensions[0]

    def getHeight(self):
        """
        Descript. :
        """
        return self.image_dimensions[1]

    def get_new_image(self):
        image = self.httpGet("?action=snapshot")
        if image is not None:
            return QtGui.QImage.fromData(image).mirrored(self.flip["h"], self.flip["v"])
        return None

    def take_snapshot(self, filename, bw=False):
        """
        Descript. :
        """
        try:   
           qimage = self.get_new_image()
           #TODO convert to grayscale
           #if bw:
           #    qimage.setNumColors(0)
           qimage.save(filename, 'PNG')
        except:
           logging.getLogger().error("MjpgStreamVideo: unable to save snapshot: %s" %filename)

    def _do_imagePolling(self, sleep_time):
        """
        Descript. :
        """ 
        while True:
            image = self.get_new_image()
            if image is not None:
                self.image = QtGui.QPixmap.fromImage(image.scaled(self.width, self.height))
                self.emit("imageReceived", self.image)
            gevent.sleep(sleep_time)
