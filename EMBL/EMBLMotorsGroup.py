"""
[Name] EMBLMotorsGroup

[Description]
The MotorsGroup Hardware Object is used to maintain several motors in one
group. Motors group is a lsit of motors which are like a grouped instance
in tine server (a tuple). It allowes to read several motor position,
statuses,... by one read.

[Channels]
- self.chanPositions
- self.chanStatus

[Commands]
- implemented as tine.set

[Emited signals]
- mGroupPosChanged
- mGroupFocModeChanged
- mGroupStatusChanged

[Functions]
- setMotorPosition()
- setMotorFocMode()
- setMotorGroupFocMode()
- stopMotor()
- positionsChanged()
- statusChanged()

[Included Hardware Objects] -

Example Hardware Object XML file :
==================================
<device class="MotorsGroup">
    <username>P14BCU</username>                     - used to identify group
    <serverAddr>/P14/P14BCU</serverAddr>            - tine server address
    <groupAddr>/ShutterTrans</groupAddr>            - motors group address
    <positionAddr>Position</positionAddr>           - position address
    <statusAddr>Status</statusAddr>                 - status address
    <motors>                                        - motors list
        <motor>
          <motorName>ShutterTrans</motorName>       - name
          <motorAddr>ShutterTrans</motorAddr>       - address
          <setCmd>MOVE.start</setCmd>               - set cmd
          <stopCmd>MOVE.stop</stopCmd>              - stop cmd
          <index>0</index>                          - index in the group
          <velocity>None</velocity>                 - velocity
          <updateTolerance>0.005</updateTolerance>  - absolute update tolerance
          <evalTolerance>0.005</evalTolerance>      - absolute tolerance of 
					              beam focus mode evaluation
          <statusModes>{'Move': 1, 'Ready': 0}</statusModes>
          <focusingModes>{'Unfocused': 0.22, 'Horizontal': 0.22, 
          'Vertical': 0.22, 'Double': 0.22}</focusingModes>
        </motor>
    </motors>
</device>"""

import time
import logging
import _tine as tine
from HardwareRepository.BaseHardwareObjects import Device 

class EMBLMotorsGroup(Device):
    """
    Descript.
    """	
    def __init__(self, name):
        Device.__init__(self, name)
        self.server_address = None
        self.group_address = None
        self.motors_list = None	
 	
        self.chan_positions = None
        self.chan_status = None

    def init(self):
        """
        Descript.
	"""
        self.server_address = self.serverAddr
        self.group_address = self.groupAddr 
        self.motors_list = []
        temp_dict = {}
        for motor in self['motors']:
            temp_dict = {}
            temp_dict['motorName'] = motor.motorName
            temp_dict['motorAddr'] = motor.motorAddr
            temp_dict['setCmd'] = motor.setCmd
            temp_dict['index'] = motor.index
            temp_dict['velocity'] = motor.velocity
            temp_dict['updateTolerance'] = motor.updateTolerance
            temp_dict['evalTolerance'] = motor.evalTolerance  
            temp_dict['statusModes'] = eval(motor.statusModes)  	
            temp_dict['focusingModes'] = eval(motor.focusingModes)	     
            temp_dict['status'] = None
            temp_dict['position'] = -9999
            temp_dict['focMode'] = []	
            self.motors_list.append(temp_dict)
        
        try:  
           self.chan_positions = self.addChannel({"type": "tine", 
                "tinename": self.server_address + self.group_address, 
                "name": self.positionAddr}, self.positionAddr)
           self.chan_positions.connectSignal('update', self.positions_changed)
        except:
           logging.getLogger("HWR").warning("EMBLMotorsGroup: unable to add channel %s/%s %s" \
                   %(self.server_address, self.group_address, self.positionAddr))
        try:
           self.chan_status = self.addChannel({"type": "tine", 
                "tinename": self.server_address + self.group_address, 
                "name": self.statusAddr}, self.statusAddr)
           self.chan_status.connectSignal('update', self.status_changed)
        except:
           logging.getLogger("HWR").warning("EMBLMotorsGroup: unable to add channel %s/%s %s" \
                   %(self.server_address, self.group_address, self.statusAddr))

    def get_motors_dict(self):
        """
        Descript.
        """
        return self.motors_list    

    def set_motor_position(self, motor_name, new_position):
        """
	Descript. : sets motor value. Direct tine.set cmd is used 
    	Arguments : motor name, new value                                        
    	Return    : -
	"""
        for motor in self.motors_list:
            if motor['motorName'] == motor_name:
                if motor['velocity'] is not None:
                    tine.set(self.server_address + "/" + motor['motorAddr'], 
                         'Velocity', motor['velocity']) 
                tine.set(self.server_address + "/" + motor['motorAddr'], 
                     motor['setCmd'], new_position)
                time.sleep(0.5)

    def set_motor_focus_mode(self, motor_name, focus_mode):
        """
    	Descript. : sets a focus mode for an individual motor
        Arguments : motor name, focus mode name                                       
        Return    : -
        """
        for motor in self.motors_list:
            if motor['motorName'] == motor_name:
                if motor['setCmd'] is not None \
                and focus_mode in motor['focusingModes'].keys():
                    if motor['velocity'] is not None:
                        tine.set(self.server_address + "/" + 
                             motor['motorAddr'], 'Velocity', motor['velocity'])
                    tine.set(self.server_address + "/" + motor['motorAddr'], 
                         motor['setCmd'], motor['focusingModes'][focus_mode])
                    time.sleep(0.5)
                break

    def set_motor_group_focus_mode(self, focus_mode):
        """
	Descript. : sets a focus mode for the motors group
    	Arguments : focus mode name                                        
    	Return    : -
	"""
        for motor in self.motors_list:
            if motor['setCmd'] is not None \
            and focus_mode in motor['focusingModes'].keys():
                if motor['velocity'] is not None:
                    tine.set(self.server_address + "/" + 
                     motor['motorAddr'], 'Velocity', motor['velocity'])
                tine.set(self.server_address + "/" + 
                     motor['motorAddr'], motor['setCmd'],
                     motor['focusingModes'][str(focus_mode)])
                time.sleep(0.5)
	       
    def stop_motor(self, motor_name):
        """
    	Descript. : stops motor movement
    	Arguments : motor name                                        
    	Return    : -
	"""
        for motor in self.motors_list:
            if motor['motorName'] == motor_name: 
                if motor['setCmd'] is not None:
                    tine.set(self.server_address + self.group_address +
                         "/" +motor_name, motor['stopCmd'])
                break
 
    def positions_changed(self, positions):
        """
        Descript. : called if one or several motors values has been changed. 
                    Evaluates if value needs to be updates, if value is 
                    changed, then evaluates focusing mode. If necessary 
                    pysignals are emited 
    	Arguments : new motor position (float) or motors positions                                       
    	Return    : -

	"""
        do_emit = False
        values_to_send = {}
        foc_mode_to_send = {}
        for motor in self.motors_list:
            old_value = motor['position']
            if type(positions) == list or type(positions) == tuple:
                new_value = positions[motor['index']]
            else:
                new_value = positions
            if abs(old_value - new_value) > motor['updateTolerance']:
                motor['position'] = new_value
                do_emit = True
            if do_emit:	
                values_to_send[motor['motorName']] = new_value
                motor['focMode'] = [] 
                for foc_mode in motor['focusingModes']:
                    diff = abs(motor['focusingModes'][foc_mode] - new_value) 
                    if diff < motor['evalTolerance']:
                        motor['focMode'].append(foc_mode)
                foc_mode_to_send[motor['motorName']] = motor['focMode'] 
        if do_emit:
            self.emit('mGroupPosChanged', str(values_to_send))
            self.emit('mGroupFocModeChanged', str(foc_mode_to_send)) 
    
    def status_changed(self, status):
        """
        Descript. : called if motors status is changed. Pysignal with new 
                    status has been sent 
        Arguments : motor status value or [motors status values]                                        
        Return    : -
        """
        values_to_send = {}
        for motor in self.motors_list:
            old_status = motor['status']
            if type(status) == list or type(status) == tuple:
                new_status = status[motor['index']]
            else:
                new_status = status
            if old_status != new_status:
                motor['status'] = new_status
                for status_mode in motor['statusModes']:
                    if motor['statusModes'][status_mode] == new_status:
                        values_to_send[motor['motorName']] = status_mode
        self.emit('mGroupStatusChanged', str(values_to_send))
