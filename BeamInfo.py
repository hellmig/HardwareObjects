"""
[Name] BeamInfo

[Description]
BeamInfo hardware object is used to define final beam size and shape.
It can include aperture, slits and/or other beam definer (lenses or other eq.)

[Emited signals]
beamInfoChanged
beamPosChanged

[Included Hardware Objects]
-----------------------------------------------------------------------
| name            | signals          | functions
-----------------------------------------------------------------------
 aperture_hwobj	    apertureChanged
 slits_hwobj	    	
 beam_definer_hwobj
-----------------------------------------------------------------------
"""

import logging
from HardwareRepository.BaseHardwareObjects import Equipment

class BeamInfo(Equipment):
    """
    Description:
    """  	

    def __init__(self, *args):
        """
        Descrip. :
        """
        Equipment.__init__(self, *args)

        self.aperture_hwobj = None
        self.slits_hwobj = None
        self.beam_definer_hwobj = None

        self.beam_size_slits = None
        self.beam_size_aperture = None
        self.beam_size_definer = None
        self.beam_position = None
        self.beam_info_dict = None
        self.default_beam_divergence = None
        self.chan_beam_size_microns = None
        self.chan_beam_shape_ellipse = None


    def init(self):
        """
        Descript. : 
        """
        self.beam_size_slits = [9999, 9999]
        self.beam_size_aperture = [9999, 9999]
        self.beam_size_definer = [9999, 9999]
        self.beam_position = [0, 0]
        self.beam_info_dict = {}

        self.aperture_hwobj = self.getObjectByRole("aperture")
        if self.aperture_hwobj is not None:
            self.connect(self.aperture_hwobj, "apertureChanged", \
                 self.aperture_pos_changed)
        else:
            logging.getLogger("HWR").debug("BeamInfo: Aperture hwobj not defined") 

        self.slits_hwobj = self.getObjectByRole("slits")
        if self.slits_hwobj is not None:  
            self.connect(self.slits_hwobj, "gapSizeChanged", self.slits_gap_changed)
        else:
            logging.getLogger("HWR").debug("BeamInfo: Slits hwobj not defined")

        self.beam_definer_hwobj = self.getObjectByRole("definer")
        if self.beam_definer_hwobj is not None:
            self.connect(self.beam_definer_hwobj, "definerPosChanged", \
                 self.definer_pos_changed)
        else:
            logging.getLogger("HWR").debug("BeamInfo: Beam definer hwobj not defined")

        default_beam_divergence_vertical = int(self.getProperty("beam_divergence_vertical"))
        default_beam_divergence_horizontal = int(self.getProperty("beam_divergence_horizontal"))
        self.default_beam_divergence = [default_beam_divergence_horizontal, default_beam_divergence_vertical]

    def get_beam_divergence_hor(self):
        """
        Descript. : 
        """
        if self.beam_definer_hwobj is not None:
            return self.beam_definer_hwobj.get_divergence_hor() 
        else:
            return self.default_beam_divergence[0]
    
    def get_beam_divergence_ver(self):
        """
        Descript. : 
        """
        if self.beam_definer_hwobj is not None:
            return self.beam_definer_hwobj.get_divergence_ver()
        else:
            return self.default_beam_divergence[1]
 
    def get_beam_position(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        raise NotImplementedError

    def set_beam_position(self, beam_x, beam_y):
        """
        Descript. :
        Arguments :
        Return    :
        """
        raise NotImplementedError

    def aperture_pos_changed(self, size):
        """
        Descript. :
        Arguments :
        Return    :
        """
        self.beam_size_aperture = size
        self.evaluate_beam_info() 
        self.emit_beam_info_change()

    def slits_gap_changed(self, size):
        """
        Descript. :
        Arguments :
        Return    :
        """
        self.beam_size_slits = size
        self.evaluate_beam_info()
        self.emit_beam_info_change()

    def definer_pos_changed(self, name, size):
        """
        Descript. :
        Arguments :
        Return    :
        """
        self.beam_size_definer = size
        self.evaluate_beam_info()
        self.emit_beam_info_change()

    def get_beam_info(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        return self.evaluate_beam_info()
        
    def get_beam_size(self):
        """
        Descript. : returns beam size in millimeters
        Return   : list with two integers
        """
        self.evaluate_beam_info()
        return self.beam_info_dict["size_x"], \
	       self.beam_info_dict["size_y"]

    def get_beam_shape(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        self.evaluate_beam_info()
        return self.beam_info_dict["shape"]

    def get_slits_gap(self):
        """
        Descript. :
        Arguments :
        Return    :
        """
        self.evaluate_beam_info()
        return self.beam_size_slits	

    def evaluate_beam_info(self):
        """
        Descript. : called if aperture, slits or focusing has been changed
        Return    : dictionary,{size_x:0.1, size_y:0.1, shape:"rectangular"}
        """
        size_x = min(self.beam_size_aperture[0],
	   	     self.beam_size_slits[0],
		     self.beam_size_definer[0]) 
        size_y = min(self.beam_size_aperture[1],
  		     self.beam_size_slits[1], 
		     self.beam_size_definer[1]) 
	
        self.beam_info_dict["size_x"] = size_x
        self.beam_info_dict["size_y"] = size_y

        # be careful with comparisons!!! both have to be the same type (=tuple)
        if tuple(self.beam_size_aperture) < tuple(self.beam_size_slits):
	    self.beam_info_dict["shape"] = "ellipse"
	else:
	    self.beam_info_dict["shape"] = "rectangular"
	
	return self.beam_info_dict	

    def emit_beam_info_change(self): 
        """
        Descript. :
        Arguments :
        Return    :
        """
        if self.beam_info_dict["size_x"] != 9999 and \
           self.beam_info_dict["size_y"] != 9999:		
            self.emit("beamSizeChanged", ((self.beam_info_dict["size_x"], \
                 self.beam_info_dict["size_y"]), ))
            self.emit("beamInfoChanged", (self.beam_info_dict, ))
            if self.chan_beam_size_microns:
                self.chan_beam_size_microns.setValue((self.beam_info_dict["size_x"] * 1000, \
                     self.beam_info_dict["size_y"] * 1000))	
            if self.chan_beam_shape_ellipse:
                self.chan_beam_shape_ellipse.setValue(self.beam_info_dict["shape"] == "ellipse") 
