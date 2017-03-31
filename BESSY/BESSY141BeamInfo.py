from HardwareRepository.BaseHardwareObjects import Equipment
from BeamInfo import BeamInfo
import logging

class BESSY141BeamInfo(BeamInfo):
    """
    Description:
    """  	

    def __init__(self,*args):
        BeamInfo.__init__(self,*args)

    def init(self):
        BeamInfo.init(self)

        self.vertpos = None
        self.horizpos = None

        self.vertpos_channel = self.getChannelObject("beam_vertical_position")
        self.horizpos_channel = self.getChannelObject("beam_horizontal_position")

        if self.vertpos_channel is not None:
           self.vertpos_channel.connectSignal("update", self.verticalPositionChanged)
        if self.horizpos_channel is not None:
           self.horizpos_channel.connectSignal("update", self.horizontalPositionChanged)

        self.evaluate_beam_info()
        self.emit_beam_info_change()

    def get_beam_position(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        logging.getLogger().info("BeamInfo. beam position requested.") 
        self.vertpos = self.vertpos_channel.getValue()
        self.horizpos = self.horizpos_channel.getValue()
        return self.horizpos, self.vertpos

    def set_beam_position(self, beam_x, beam_y):
        """
        Descript. :
        Arguments :
        Return    :
        """
        raise NotImplementedError

    def horizontalPositionChanged(self,value):
        logging.getLogger().info("Horizontal beam position changed. It is %s" % str(value))
        self.horizpos = self.horizpos_channel.getValue()
        if self.vertpos is not None:
            self.emit("beamPosChanged", ([self.horizpos, self.vertpos]))
            self.emit("beamPositionChanged", ([self.horizpos, self.vertpos]))
            self.emit_beam_info_change()

    def verticalPositionChanged(self,value):
        logging.getLogger().info("Vertical beam position changed. It is %s" % str(value))
        self.vertpos = self.vertpos_channel.getValue()
        if self.horizpos is not None:
            self.emit("beamPosChanged", ([self.horizpos, self.vertpos]))
            self.emit("beamPositionChanged", ([self.horizpos, self.vertpos]))
            self.emit_beam_info_change()

    def aperture_pos_changed(self, pos, size):
        """
        Descript. :
        Arguments :
        Return    :
        """
        # print "BESSY141BeamInfo.aperture_pos_changed", pos, size
        self.beam_size_aperture = size
        self.evaluate_beam_info() 
        self.emit_beam_info_change()

