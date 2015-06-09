
from HardwareRepository.BaseHardwareObjects import Equipment
from BeamInfo import BeamInfo

class BESSY141BeamInfo(BeamInfo):
    """
    Description:
    """  	

    def __init__(self,*args):
        BeamInfo.__init__(self,*args)

    def init(self):
        self.vertpos_channel = self.getChannelObject("beam_vertical_position")
        self.horizpos_channel = self.getChannelObject("beam_horizontal_position")

        if self.vertpos_channel is not None and self.horizpos_channel is not None:
            if self.vertpos_channel is not None:
                self.vertpos_channel.connectSignal("update", self.verticalPositionChanged)
            if self.horizpos_channel is not None:
                self.horizpos_channel.connectSignal("update", self.horizontalPositionChanged)
        BeamInfo.init(self)
        self.beam_size_aperture  = [70,70] 
        self.evaluate_beam_info()
        self.emit_beam_info_change()

    def get_beam_position(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        vertpos = self.vertpos_channel.getValue()
        horizpos = self.horizpos_channel.getValue()
        return horizpos, vertpos

    def set_beam_position(self, beam_x, beam_y):
        """
        Descript. :
        Arguments :
        Return    :
        """
        raise NotImplementedError

    def horizontalPositionChanged(self,value):
        logging.getLogger().debug("Horizontal beam position changed. It is %s" % str(value))

    def verticalPositionChanged(self,value):
        logging.getLogger().debug("Vertical beam position changed. It is %s" % str(value))
