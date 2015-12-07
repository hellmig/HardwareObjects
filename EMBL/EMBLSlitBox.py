#Last change: 2014.09.04 - Ivars Karpics (EMBL Hamburg)
"""
[Name] BeamSlitBox

[Description]
The BeamSlitBox Hardware Object is used to operate slits.

[Channels] -

[Commands] -

[Emited signals]
- statusChanged
- focModeChanged
- gapLimitsChanged
- gapSizeChanged  

[Functions]
- getShape()
- getStepSizes()
- getMinGaps()
- getMaxGaps()
- getGapLimits()
- changeMotorPos()
- mGroupStatusChanged()
- mGroupPosChanged()
- getGapHor()
- getGapVer()
- setGap()
- stopGapHorChange()
- setFocusingMode()
- focModeChanged()
- setGapLimits()

[Hardware Objects]      
-----------------------------------------------------------------------
| name         | signals             | functions
|----------------------------------------------------------------------
| MotorsGroup  | mGroupPosChanged    | setMotorPosition()
|              | mGroupStatusChanged | stopMotor()
|	       |		     | setMotorFocMode()	
|----------------------------------------------------------------------
| BeamFocusing | focusModeChanged    |
-----------------------------------------------------------------------

Example Hardware Object XML file :
==================================
<equipment class="BeamSlitBox">
    <focModeEq>/beamFocusing</focModeEq>             - focusing mode equipment
    <focModes>['Unfocused', 'Horizontal', 'Vertical', 'Double']</focModes> 
                                                     - used focusing modes
    <gapH>                                           
       <modesAllowed>['Unfocused', 'Vertical']</modesAllowed> - used modes
       <stepSize>0.0050</stepSize>                   - step size used in spinbox
       <minGap>0.010</minGap>                        - min gap
       <maxGap>1.10</maxGap>                         - max max gap
       <updateTolerance>0.0005</updateTolerance>     - gap update tolerance
       <motors>                                      - motors used to define gap
          <motor>
            <motorName>Out</motorName>               - name
            <motorsGroup>attocubeMotors</motorsGroup>- motors group name
            <reference>407154</reference>            - reference value
          </motor>
          <motor>
            <motorName>In</motorName>
            <motorsGroup>attocubeMotors</motorsGroup>
            <reference>-68579</reference>
          </motor>
       </motors>
    </gapH>
    <gapV>                                              
       <modesAllowed>['Unfocused', 'Horizontal']</modesAllowed>
       <stepSize>0.0050</stepSize>
       <minGap>0.010</minGap>
       <maxGap>1.10</maxGap>
       <updateTolerance>0.0005</updateTolerance>
       <motors>
          <motor>
            <motorName>Top</motorName>
            <motorsGroup>attocubeMotors</motorsGroup>
            <reference>66114</reference>
          </motor>
          <motor>
            <motorName>But</motorName>
            <motorsGroup>attocubeMotors</motorsGroup>
            <reference>4391</reference>
          </motor>
       </motors>
    </gapV>
    <device hwrid="/attocubeMotors/attoGroup" role="attocubeMotors"/>
</equipment>
"""
import logging
from HardwareRepository.BaseHardwareObjects import Equipment
from HardwareRepository import HardwareRepository

class EMBLSlitBox(Equipment):
    """
    Descript. : User can define sizes of horizontal and verstical slits by 
                entering direct size and pressing Enter or by using up and 
                down buttons. Slits operations are enabled accordingly to 
                the detected focusing mode.
                  - Unfocused beam (both enabled)
                  - Horizontally focused (hor. disabled and ver. enabled)			
                  - Vertically focused (hor. enabled and ver. disabled)
                  - Double focused (both disabled)
                User can stop slit movement by pressing stop button 
                (enabled if slits moves).	
    """	
    def __init__(self, *args):
        """
        Decript. :
        """
	Equipment.__init__(self, *args)
        self.decimal_places = None
        self.active_focus_mode = None       
        self.beam_focus_hwobj = None  
        self.gaps_dict = None
        self.motors_dict = None
        self.init_max_gaps = None
        self.motors_groups = None
        self.hor_gap = False
        self.ver_gap = False
	
    def init(self):
        """
        Descript. 
        """
        self.decimal_places = 6
        self.gaps_dict = {}
        self.gaps_dict['Hor'] = self['gapH'].getProperties()
        self.gaps_dict['Ver'] = self['gapV'].getProperties()
        self.gaps_dict['Hor']['value'] = 0.10
        self.gaps_dict['Ver']['value'] = 0.10
        self.gaps_dict['Hor']['status'] = ''
        self.gaps_dict['Ver']['status'] = ''
        self.init_max_gaps = self.get_max_gaps()

        self.motors_dict = {}
        for motor in self['gapH']['motors']:
            self.motors_dict[motor.motorName] = {}
            self.motors_dict[motor.motorName]['motorsGroup'] = motor.motorsGroup 
            self.motors_dict[motor.motorName]['gap'] = 'Hor'
            self.motors_dict[motor.motorName]['reference'] = motor.reference
            self.motors_dict[motor.motorName]['position'] = 0
            self.motors_dict[motor.motorName]['status'] = None
            self.motors_dict[motor.motorName]['focMode'] = []

        for motor in self['gapV']['motors']: 
            self.motors_dict[motor.motorName] = {}
            self.motors_dict[motor.motorName]['motorsGroup'] = motor.motorsGroup 
            self.motors_dict[motor.motorName]['gap'] = 'Ver'
            self.motors_dict[motor.motorName]['reference'] = motor.reference
            self.motors_dict[motor.motorName]['position'] = 0
            self.motors_dict[motor.motorName]['status'] = None
            self.motors_dict[motor.motorName]['focMode'] = []	 

        
        self.motors_groups = self.getDevices()
        if self.motors_groups is not None:
            for motor_group in self.motors_groups:
                self.connect(motor_group, 'mGroupPosChanged', 
                     self.motors_group_position_changed)
                self.connect(motor_group, 'mGroupStatusChanged', 
                     self.motors_group_status_changed)
        if True: 
            self.beam_focus_hwobj = HardwareRepository.HardwareRepository().\
                 getHardwareObject(self.getProperty('focModeEq'))
            self.connect(self.beam_focus_hwobj, 'definerPosChanged', self.focus_mode_changed)
            self.active_focus_mode = self.beam_focus_hwobj.get_active_focus_mode()
        #except:
        #    logging.getLogger("HWR").debug('BeamSlitBox: beamFocus HO not defined')

    def get_step_sizes(self):
        """
        Descript. : returns Hor and Ver step sizes
        Arguments : -                                        
        Return    : step size values (list of two values)
        """
        return [self.gaps_dict['Hor']['stepSize'], 
                self.gaps_dict['Ver']['stepSize']]

    def get_min_gaps(self):
        """
        Descript. : returns min Hor and Ver gaps values
        Arguments : -                                        
        Return    : min gap values (list of two values)
        """
        return [self.gaps_dict['Hor']['minGap'], 
                self.gaps_dict['Ver']['minGap']]		

    def get_max_gaps(self):
        """
        Descript. : returns max Hor and Ver gaps values
        Arguments : -                                        
        Return    : max gap values (list of two values)
	"""
        return [self.gaps_dict['Hor']['maxGap'], 
                self.gaps_dict['Ver']['maxGap']] 	

    def get_gap_limits(self, gap_name):
        """
        Descript. : returns gap min and max limits
        Arguments : gap name                                        
        Return    : min and max gap values (list of two values)
        """
        return [self.gaps_dict[gap_name]['minGap'],
                self.gaps_dict[gap_name]['maxGap']]           

    def change_motor_position(self, motor_name, position):
        """
        Descript. : cmd to set motor position
        Arguments : motor name (string), new value(float)                                        
        Return    : -
        """
        for motors_group in self.motors_groups:
            if self.motors_dict[motor_name]['motorsGroup'] == motors_group.userName():	
                motors_group.set_motor_position(motor_name, position)
                return

    def motors_group_status_changed(self, new_status_dict):
        """
        Descript. : function called if motors group status is changed
        Arguments : new status (string)                                        
        Return    : -
        """
        new_status_dict = eval(new_status_dict)
        for motor in new_status_dict: 
            if motor in self.motors_dict:
                self.motors_dict[motor]['status'] = new_status_dict[motor]
                self.gaps_dict[self.motors_dict[motor]['gap']]['status'] = \
                     new_status_dict[motor]
        self.emit('statusChanged', (self.gaps_dict['Hor']['status'], 
                                    self.gaps_dict['Ver']['status']))

    def motors_group_position_changed(self, new_positions_dict):
        """
        Descrip. : function called if one or sever motors value/s are changed
        Arguments: motors values (list of float values)                                     
        Return   : -
        """
        new_positions_dict = eval(new_positions_dict)
        for motor in new_positions_dict:
            self.motors_dict[motor]['position'] = new_positions_dict[motor]
        self.gaps_dict['Hor']['value'] = self.get_gap_hor()
        self.gaps_dict['Ver']['value'] = self.get_gap_ver()
        self.emit('gapSizeChanged', [self.gaps_dict['Hor']['value'], 
                                     self.gaps_dict['Ver']['value']])

    def get_gap_hor(self):
        """
        Descript. : evaluates Horizontal gap
        Arguments : -                                        
        Return    : Hor gap value in mm 
        """
        gap = self.motors_dict['In']['position'] - \
              self.motors_dict['In']['reference'] + \
              self.motors_dict['Out']['position'] - \
              self.motors_dict['Out']['reference']
        gap = - gap / (10**self.decimal_places)
        return gap

    def get_gap_ver(self):
        """
        Descript. : evaluates Vertical gap
        Arguments : -                                        
        Return    : Ver gap value in mm
        """
        gap = self.motors_dict['Top']['position'] - \
              self.motors_dict['Top']['reference'] + \
              self.motors_dict['But']['position'] - \
              self.motors_dict['But']['reference']
        gap = - gap / (10**self.decimal_places)
        return gap
   
    def get_gaps(self):
        """
        Descript.
        """
        return 'Horizontal: %0.3f' % self.get_gap_hor() + \
               ' Vertical: %0.3f' % self.get_gap_ver()
	
    def set_gap(self, gap_name, new_gap):
        """
        Descript. : sets new gap value
        Arguments : gap name(string), gap value(float)                                        
        Return    : -
        """
        old_gap = self.gaps_dict[gap_name]['value']
        if abs(old_gap - new_gap) > self.gaps_dict[gap_name]['updateTolerance']:
            for motor in self.motors_dict:
                if self.motors_dict[motor]['gap'] == gap_name:
                    if new_gap > old_gap:
                        new_position = self.motors_dict[motor]['position'] - \
                        float((new_gap - old_gap) / 2 * (10 ** self.decimal_places))
                    else:
                        new_position = self.motors_dict[motor]['position'] + \
                        float((old_gap - new_gap) / 2 * (10 ** self.decimal_places))		
                    for motor_group in self.motors_groups:
                        if self.motors_dict[motor]['motorsGroup'] == motor_group.userName():
                            motor_group.set_motor_position(motor, new_position)
                            break

    def stop_gap_move(self, gap_name):
        """
        Descript.: stops motors movements
        Arguments: gap name(string)                                        
        Return   : -
        """
        for motor in self.motors_dict:
            for motors_group in self.motors_groups:
                if motor['motorsGroup'] == motors_group.userName(): 
                    if motor['gap'] == gap_name:
                        motors_group.stop_motor(motor['motorName'])

    def set_focus_mode(self, focus_mode):
        """
        Descript. : sets motors in possitions according to focusing mode
        Arguments : focusing mode(string)                                        
        Return    : -
        """
        self.active_focus_mode = focus_mode
        for motor in self.motors_dict:
            for motors_group in self.motors_groups_devices:
                if self.motors_dict[motor]['motorsGroup'] == motors_group.userName(): 
                    motors_group.set_motor_focus_mode(motor, focus_mode)

    def focus_mode_changed(self, new_focus_mode, size):
        """
        Descript. : called if focusing mode is changed
        Arguments : new focusinf mode (string)                                        
        Return    : - 
        """
        if self.active_focus_mode != new_focus_mode:
            self.hor_gap = False
            self.ver_gap = False
            self.active_focus_mode = new_focus_mode
            if self.active_focus_mode is not None:
                if self.active_focus_mode in self.gaps_dict['Hor']['modesAllowed']: 
                    self.hor_gap = True
                if self.active_focus_mode in self.gaps_dict['Ver']['modesAllowed']: 
                    self.ver_gap = True
            self.emit('focModeChanged', (self.hor_gap, self.ver_gap))

    def set_gaps_limits(self, new_gaps_limits):
        """
        Descript. : sets max gap Limits
        Arguments : [max Hor gap, max Ver gap (list of two float values)                                        
        Return    : -
        """
        if new_gaps_limits is not None:
            self.gaps_dict['Hor']['maxGap'] = min(self.init_max_gaps[0], new_gaps_limits[0])
            self.gaps_dict['Ver']['maxGap'] = min(self.init_max_gaps[1], new_gaps_limits[1])	
            self.emit('gapLimitsChanged', [self.gaps_dict['Hor']['maxGap'], 
                                           self.gaps_dict['Ver']['maxGap']])

    def update_values(self):
        self.emit('focModeChanged', (self.hor_gap, self.ver_gap)) 
        self.emit('gapSizeChanged', [self.gaps_dict['Hor']['value'],
                                     self.gaps_dict['Ver']['value']])

