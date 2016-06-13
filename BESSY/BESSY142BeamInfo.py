from HardwareRepository.BaseHardwareObjects import Equipment
from BeamInfo import BeamInfo
import logging

class BESSY142BeamInfo(BeamInfo):
    """
    Description:
    """  	

    def __init__(self,*args):
        BeamInfo.__init__(self,*args)

    def init(self):
        BeamInfo.init(self)
        self.beam_size_aperture = (250, 100)
        self.evaluate_beam_info()
        self.emit_beam_info_change()

    def get_beam_position(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        logging.getLogger().info("BeamInfo. beam position requested.") 
        return (330, 247)

    def set_beam_position(self, beam_x, beam_y):
        """
        Descript. :
        Arguments :
        Return    :
        """
        raise NotImplementedError

