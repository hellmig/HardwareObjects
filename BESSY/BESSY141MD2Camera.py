import gevent

from PyQt4 import QtGui
from PyQt4 import QtCore

from HardwareRepository.BaseHardwareObjects import Device
import math
import logging
import gevent
import array
import time

class BESSY141MD2Camera(Device):      

    def __init__(self, name):
        Device.__init__(self, name)
        self.setIsReady(True)
 
    def init(self): 
        logging.getLogger("HWR").info("BESSY141MD2Camera: initializing camera hardware object.")

        self.forceUpdate = None
        self.image_polling = None

        self.pollInterval = 40
        if self.getProperty("interval"):
            self.pollInterval = self.getProperty("interval")

        self.get_image_cmd = self.getCommandObject("get_image_cmd")

        self.stopper = False

        if self.image_polling is None:
            self.image_polling = gevent.spawn(self.do_image_polling, self.pollInterval/1000.0)

    def do_image_polling(self, sleep_time):
        while (True):
            try:
                self.get_new_image()
            except:
                logging.getLogger("HWR").exception("BESSY141MD2Camera: Could not read image")
            else:
                pass
            finally:
                gevent.sleep(sleep_time)

    def getImage(self):
          return self.get_image_cmd()

    def gammaExists(self):
        return False

    def contrastExists(self):
        return False

    def brightnessExists(self):
        return False

    def gainExists(self):
        return False

    def getWidth(self):
        return 1360 # 2017-02-24-mh

    def getHeight(self):
        return 1024 # 2017-02-24-mh

    def setLive(self, state):
        self.liveState = state
        return True

    def imageType(self):
        return None

    def takeSnapshot(self,snapshot_filename, bw=True):
        img = self.get_image_cmd()
        img_array = array.array('b', img)
        img_str = imgArray.tostring()
        f=open(snapshot_filename, "wb") 
        f.write(img_str)
        f.close() 
        return True

    def get_snapshot_img_str(self):
        img = self.get_image_cmd()
        img_array = array.array('b', img)
        img_str = imgArray.tostring()
        return img_str

    def get_image_dimensions(self):
        return list((1360, 1024))

    def start_camera(self):
        return 

    def get_new_image(self):
        """
        Descript. :
        """
        image = self.get_image_cmd()

        qimage = QtGui.QImage.fromData(image)
        qpixmap = QtGui.QPixmap.fromImage(qimage)
        self.emit("imageReceived", qpixmap)

