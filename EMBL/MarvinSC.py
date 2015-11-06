"""
[Name] MarvinSC

[Description]
Hardware object for Marvin sample changer

[Channels]

[Commands]

[Emited signals]

[Included Hardware Objects]
-----------------------------------------------------------------------
| name            | signals          | functions
-----------------------------------------------------------------------
-----------------------------------------------------------------------
"""

from sample_changer.GenericSampleChanger import *


class MarvinSC(SampleChanger):
    """
    """    
    __TYPE__ = "Marvin"    

    def __init__(self, *args, **kwargs):
        super(MarvinSC, self).__init__(self.__TYPE__,False, *args, **kwargs)
        self._selected_sample = None
        self._selected_basket = None
        self._scIsCharging = None

        self._num_baskets = None
        self._status_string = None
        self._state_string = None
        self._puck_switches = None
        self._mounted_puck = None
        self._mounted_sample = None
        self._sample_is_mounted = None
        self._progress = None

        self.chan_status = None
        self.chan_puck_switched = None
        self.chan_mounted_sample_puck = None

        self.cmd_mount_sample = None
        self.cmd_unmount_sample = None
        self.cmd_dry_gripper = None
            
    def init(self):      
        self._puck_switches = 0
        self._num_basket = self.getProperty("numBaskets")
        if not self._num_basket:
            self._num_basket = 10

        for i in range(self._num_basket):
            basket = Basket(self, i + 1)
            self._addComponent(basket)

        self.chan_puck_switches = self.getChannelObject("chanPuckSwitches")
        if self.chan_puck_switches is not None:
            self.chan_puck_switches.connectSignal("update", self.puck_switches_changed)

        self.chan_status = self.getChannelObject("chanStatus")
        if self.chan_status is not None:
            self.chan_status.connectSignal("update", self.status_string_changed)

        self.chan_mounted_sample_puck = self.getChannelObject("chanMountedSamplePuck")
        if self.chan_mounted_sample_puck is not None:
            self.chan_mounted_sample_puck.connectSignal("update", self.mounted_sample_puck_changed)

        self.cmd_mount_sample = self.getCommandObject("cmdMountSample")
        self.cmd_unmount_sample = self.getCommandObject("cmdUnmountSample")

        """if None in (self.chan_puck_switches, self.chan_status, \
             self.cmd_mount_sample, self.cmd_unmount_sample):
            msg = "Sample changer not initialized. "
            msg += "Please check the communication to sample changer and restart MXCuBE"
            logging.getLogger("user_level_log").error(msg)"""

        self._initSCContents()
        SampleChanger.init(self)  

    def puck_switches_changed(self, puck_switches):
        self._puck_switches = int(puck_switches)
        self._updateSCContents()

    def mounted_sample_puck_changed(self, mounted_sample_puck):
        self._mounted_sample = mounted_sample_puck[0] -1 
        self._mounted_puck = mounted_sample_puck[1] -1 
        self._updateLoadedSample()

    def getSampleProperties(self):
        return (Pin.__HOLDER_LENGTH_PROPERTY__,)
        
    def _doUpdateInfo(self):       
        """
        Descript. : Updates the sample changers status: mounted pucks, 
                    state, currently loaded sample
        """
        pass
        #self._updateState()               
        #self._updateSCContents()
        #call this method if status string changed
        #self._updateLoadedSample()
                    
    def _directlyUpdateSelectedComponent(self, basket_no, sample_no):    
        basket = None
        sample = None
        try:
          if basket_no is not None and basket_no>0 and basket_no <=self._num_basket:
            basket = self.getComponentByAddress(Basket.getBasketAddress(basket_no))
            if sample_no is not None and sample_no>0 and sample_no <=Basket.NO_OF_SAMPLES_PER_PUCK:
                sample = self.getComponentByAddress(Pin.getSampleAddress(basket_no, sample_no))            
        except:
          pass
        self._setSelectedComponent(basket)
        self._setSelectedSample(sample)

    def _doSelect(self,component):
        """
        Descript. : Selects a new component (basket or sample).
                    Uses method >_directlyUpdateSelectedComponent< to actually 
                    search and select the corrected positions.
        """
        if isinstance(component, Sample):
            selected_basket_no = component.getBasketNo()
            selected_sample_no = component.getIndex()+1
        elif isinstance(component, Container) and ( component.getType() == Basket.__TYPE__):
            selected_basket_no = component.getIndex()+1
            selected_sample_no = None
        self._directlyUpdateSelectedComponent(selected_basket_no, selected_sample_no)
            
    def _doScan(self,component,recursive):
        """
        Descript. : Scans the barcode of a single sample, puck or 
                    recursively even the complete sample changer.
        """
        print "_doScan TODO"
    
    def _doLoad(self,sample=None):
        """
        Descript. : Loads a sample on the diffractometer. 
                    Performs a simple put operation if the diffractometer is 
                    empty, and a sample exchange (unmount of old + mount of 
                    new sample) if a sample is already mounted on the diffractometer.
        """
        selected=self.getSelectedSample()            

        if sample is not None:
            if sample != selected:
                self._doSelect(sample)
                selected=self.getSelectedSample()            
        else:
            if selected is not None:
                 sample = selected
            else:
               raise Exception("No sample selected")

        basket = selected.getBasketNo() 
        sample = selected.getVialNo()
       
        if self.hasLoadedSample():
            if selected==self.getLoadedSample():
                msq = "The sample " + \
                      str(self.getLoadedSample().getAddress()) + \
                      " is already loaded"
                raise Exception(msg)
            else:
                self._executeServerTask(self.cmd_unmount_sample, self._mounted_sample, self._mounted_puck)
                self._executeServerTask(self.cmd_mount_sample, int(sample), int(basket))
        else:
            self._executeServerTask(self.cmd_mount_sample, int(sample), int(basket))

    def _doUnload(self, sample_slot = None):
        """
        Descript. : Unloads a sample from the diffractometer.
        """
        #self.cmd_unmount_sample(self._mounted_sample, self._mounted_puck)
        #if (sample_slot is not None):
        #    self._doSelect(sample_slot)
        self._executeServerTask(self.cmd_unmount_sample, int(self._mounted_sample), int(self._mounted_puck))

    def clearBasketInfo(self, basket):
        return

    #def load_sample(self, *args, **kwargs):
    #    kwargs["wait"] = True
    #    return self.load(*args, **kwargs)

    def _doChangeMode(self, mode):
        return

    def _doAbort(self):
        """
        Descript. : Aborts a running trajectory on the sample changer.
        """
        return

    def _doReset(self):
        """
        Descript. : Clean all sample info, move sample to his position
                    and move puck from center to base
        """
        self._initSCContents() 

    def _updateOperationMode(self, value):
        self._scIsCharging = not value

    def _executeServerTask(self, method, *args):
        self._waitDeviceReady(3.0)
        self._state_string = "Bsy"
        self.emit("progressInit", ("Sample changer", 100))
        #task_id = method(*args)
        arg_arr = []
        for arg in args:
            arg_arr.append(arg) 
        task_id = method(arg_arr)
        ret=None

        if task_id is None: #Reset
            while self._isDeviceBusy():
                gevent.sleep(0.1)
        else:
            # introduced wait because it takes some time before the attribute PathRunning is set
            # after launching a transfer
            time.sleep(2.0)
            self._waitDeviceReady(3.0)
            #hile self.state != SampleChangerState.Ready: 
            #   gevent.sleep(0.1)            
            ret = True
        gevent.sleep(2)
        return ret

    def _updateState(self):
        state = self._readState()
        if (state == SampleChangerState.Moving and 
            self._isDeviceBusy(self.getState())):
            return
        self._setState(state)
       
    def _readState(self):
        """
        Descript. : converts state string to defined sc state
        """
        state_converter = { "ALARM": SampleChangerState.Alarm,
                            "Idl": SampleChangerState.Ready,
                            "Bsy": SampleChangerState.Moving }
        return state_converter.get(self._state_string, SampleChangerState.Unknown)
                        
    def _isDeviceBusy(self, state=None):
        """
        Descript : Checks whether Sample changer HO is busy.
        """
        if state is None:
            state = self._readState()
        if self._progress >= 100 and state in (SampleChangerState.Ready, 
                                               SampleChangerState.Loaded,
                                               SampleChangerState.Alarm, 
                                               SampleChangerState.Disabled, 
                                               SampleChangerState.Fault, 
                                               SampleChangerState.StandBy):
            return False
        else:
            return True

    def _isDeviceReady(self):
        """
        Descript : Checks whether Sample changer HO is ready.
        """
        state = self._readState()
        return state in (SampleChangerState.Ready, SampleChangerState.Charging)              

    def _waitDeviceReady(self,timeout=None):
        """
        Descript. : Waits until the samle changer HO is ready.
        """
        with gevent.Timeout(timeout, Exception("Timeout waiting for device ready")):
            while not self._isDeviceReady():
                gevent.sleep(1)
                #gevent.sleep(0.01)
            
    def _updateSelection(self):    
        """
        Descript. : Updates selected basked and sample 
        """
        basket=None
        sample=None
        try:
          basket_no = self._selected_basket
          if basket_no is not None and basket_no>0 and basket_no <= self._num_basket:
            basket = self.getComponentByAddress(Basket.getBasketAddress(basket_no))
            sample_no = self._selected_sample
            if sample_no is not None and sample_no>0 and sample_no <= Basket.NO_OF_SAMPLES_PER_PUCK:
                sample = self.getComponentByAddress(Pin.getSampleAddress(basket_no, sample_no))            
        except:
          pass
        self._setSelectedComponent(basket)
        self._setSelectedSample(sample)

    def _updateLoadedSample(self):
        """
        Descript. : updates loaded sample
        """
        if not self._sample_is_mounted:
            new_sample = None
        elif self._mounted_puck and self._mounted_sample:
            new_sample = self.getComponentByAddress(\
                  Pin.getSampleAddress(self._mounted_puck, self._mounted_sample))
        else:
            new_sample = None

        if self.getLoadedSample() != new_sample:
            # import pdb; pdb.set_trace()
            # remove 'loaded' flag from old sample but keep all other information
            old_sample = self.getLoadedSample()
            if old_sample is not None:
                # there was a sample on the gonio
                loaded = False
                has_been_loaded = True
                old_sample._setLoaded(loaded, has_been_loaded)
            if new_sample is not None:
                self._updateSampleBarcode(new_sample)
                loaded = True
                has_been_loaded = True
                new_sample._setLoaded(loaded, has_been_loaded)

    def _updateSampleBarcode(self, sample):
        """
        Descript : Updates the barcode of >sample< in the local database 
                   after scanning with the barcode reader.
        """
        datamatrix = "NotAvailable"
        scanned = (len(datamatrix) != 0)
        if not scanned:    
           datamatrix = '----------'   
        sample._setInfo(sample.isPresent(), datamatrix, scanned)

    def _initSCContents(self):
        """
        Descript : Initializes the sample changer content with default values.
        """
        basket_list= [('', 4)] * self._num_basket
        for basket_index in range(self._num_basket):            
            basket=self.getComponents()[basket_index]
            datamatrix = None
            present = scanned = False
            basket._setInfo(present, datamatrix, scanned)

        # create temporary list with default sample information and indices
        sample_list=[]
        for basket_index in range(self._num_basket):            
            for sample_index in range(10):
                sample_list.append(("", basket_index+1, sample_index+1, 1, Pin.STD_HOLDERLENGTH)) 
        # write the default sample information into permanent Pin objects 
        for spl in sample_list:
            sample = self.getComponentByAddress(Pin.getSampleAddress(spl[1], spl[2]))
            datamatrix = None
            present = scanned = loaded = has_been_loaded = False
            sample._setInfo(present, datamatrix, scanned)
            sample._setLoaded(loaded, has_been_loaded)
            sample._setHolderLength(spl[4])    

    def _updateSCContents(self):
        """
        """
        for basket_index in range(self._num_basket):            
            basket=self.getComponents()[basket_index]

            if (int(self._puck_switches) & pow(2, basket_index) > 0) or \
               (self._mounted_puck == basket_index + 1):
            #f puck_switches & (1 << basket_index):
                # basket was mounted
                present = True
                scanned = False
                datamatrix = None
            else:
                # basket was removed
                present = False
                scanned = False
                datamatrix = None
            basket._setInfo(present, datamatrix, scanned)
            # set the information for all dependent samples
            for sample_index in range(Basket.NO_OF_SAMPLES_PER_PUCK):
                sample = self.getComponentByAddress(Pin.getSampleAddress((basket_index + 1), (sample_index + 1)))
                present = sample.getContainer().isPresent()
                if present:
                    datamatrix = '%d:%d - Not defined' %(basket_index,sample_index)
                else:
                    datamatrix = None
                datamatrix = None
                scanned = False
                sample._setInfo(present, datamatrix, scanned)
                # forget about any loaded state in newly mounted or removed basket)
                loaded = has_been_loaded = False
                sample._setLoaded(loaded, has_been_loaded)

    def status_string_changed(self, status_string):
        """
        Descript. : status string change event. Converts status string to all
                    parameters.
                    lid    : LidCls, LidOpn, LidBus
                    magnet : MagOff, MagOn
                    cryo   : CryoErr
                    centralPuck  : None, no.
                    isSample : SmpleYes, SmplNo 
        """
        self._status_string = status_string[:180].replace(" ", "")

        status_list = self._status_string.split(';')
        for status in status_list: 
            property_status_list = status.split(':')
            if len(property_status_list) < 2:
                continue
            prop_name = property_status_list[0]
            prop_value = property_status_list[1]
            if prop_name == "Rob":
                if self._state_string != prop_value:
                    self._state_string = prop_value
                    self._updateState()
            elif prop_name == "MD":  
                sample_is_mounted = prop_value == "Mount"
                if self._sample_is_mounted != sample_is_mounted:
                    self._sample_is_mounted = sample_is_mounted
                    if not self._sample_is_mounted:
                        self._mounted_sample = -1
                    self._updateLoadedSample()
            elif prop_name == "Prgs":
                if int(prop_value) != self._progress:
                    self._progress = int(prop_value)
                    self.emit("progressStep", self._progress)
