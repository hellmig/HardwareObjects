"""
Isara2 sample changer hardware object.

Implements the abstract interface of the GenericSampleChanger for the Irelec Isara2
sample changer model.
Copy of CATS implementation.
Derived from Alexandre Gobbo's implementation for the EMBL SC3 sample changer.
"""
from sample_changer.GenericSampleChanger import *
import time

__author__ = "Michael Hellmig"
__credits__ = ["The MxCuBE collaboration"]

__email__ = "michael.hellmig@helmholtz-berlin.de"
__status__ = "Beta"

class Pin(Sample):        
    STD_HOLDERLENGTH = 22.0

    def __init__(self,basket,basket_no,sample_no):
        super(Pin, self).__init__(basket, Pin.getSampleAddress(basket_no,sample_no), False)
        self._setHolderLength(Pin.STD_HOLDERLENGTH)

    def getBasketNo(self):
        return self.getContainer().getIndex()+1

    def getVialNo(self):
        return self.getIndex()+1

    @staticmethod
    def getSampleAddress(basket_number, sample_number):
        return str(basket_number) + ":" + "%02d" % (sample_number)


class Basket(Container):
    __TYPE__ = "Puck"    
    NO_OF_SAMPLES_PER_PUCK = 16

    def __init__(self,container,number):
        super(Basket, self).__init__(self.__TYPE__,container,Basket.getBasketAddress(number),False)
        for i in range(Basket.NO_OF_SAMPLES_PER_PUCK):
            slot = Pin(self,number,i+1)
            self._addComponent(slot)
                            
    @staticmethod
    def getBasketAddress(basket_number):
        return str(basket_number)

    def clearInfo(self):
	self.getContainer()._reset_basket_info(self.getIndex()+1)
        self.getContainer()._triggerInfoChangedEvent()


class Isara2(SampleChanger):
    """
    Actual implementation of the Isara2 Sample Changer,
    BESSY BL14.2 installation with 1 lid and 464 samples (Unipuck)
    """    
    __TYPE__ = "ISARA2"    
    NO_OF_LIDS = 1
    NO_OF_BASKETS = 29
    TOOL_ID = "3"

    def __init__(self, *args, **kwargs):
        super(Isara2, self).__init__(self.__TYPE__,False, *args, **kwargs)
            
    def init(self):      
        self._selected_sample = None
        self._selected_basket = None
        self._scIsCharging = None

        # initialize the sample changer components, moved here from __init__ after allowing
        # variable number of lids
        for i in range(Isara2.NO_OF_BASKETS):
            basket = Basket(self,i+1)
            self._addComponent(basket)

        for channel_name in ("_chnState", "_chnPowered", "_chnNumLoadedSample", "_chnPuckLoadedSample", "_chnSampleBarcode", "_chnPathRunning", "_chnSampleIsDetected", "_chnLidOpened", "_chnPuckPresence"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
           
        for command_name in ("_cmdAbort", "_cmdLoad", "_cmdUnload", "_cmdChainedLoad"):
            setattr(self, command_name, self.getCommandObject(command_name))

        self._initSCContents()

        # SampleChanger.init must be called _after_ initialization of the Cats because it starts the update methods which access
        # the device server's status attributes
        SampleChanger.init(self)   

    def getSampleProperties(self):
        """
        Get the sample's holder length

        :returns: sample length [mm]
        :rtype: double
        """
        return (Pin.__HOLDER_LENGTH_PROPERTY__,)

    def getBasketList(self):
        basket_list = []
        for basket in self.getComponents():
            if isinstance(basket, Basket):
                basket_list.append(basket)
        return basket_list

    def select(self, component, wait=True):
        """
        Overwrite select method of the GenericSampleChanger because the ISARA saves the information of the 
        selected basket and sample in the hardware object only.
        A separate task is not needed here.

        :returns: 
        :rtype: integer
        """
        component = self._resolveComponent(component)
        self._doSelect(component)
        self._triggerSelectionChangedEvent()        
        return 0
        
    #########################           TASKS           #########################

    def _doUpdateInfo(self):       
        """
        Updates the sample changers status: mounted pucks, state, currently loaded sample

        :returns: None
        :rtype: None
        """
        self._updateSCContents()
        # periodically updating the selection is not needed anymore, because each call to _doSelect
        # updates the selected component directly:
        # self._updateSelection()
        self._updateState()               
        self._updateLoadedSample()
                    
    def _doChangeMode(self,mode):
        """
        Changes the SC operation mode, not implemented for the ISARA system

        :returns: None
        :rtype: None
        """
        pass

    def _directlyUpdateSelectedComponent(self, basket_no, sample_no):    
        basket = None
        sample = None
        try:
          if basket_no is not None and (basket_no > 0) and (basket_no <= Isara2.NO_OF_BASKETS):
            basket = self.getComponentByAddress(Basket.getBasketAddress(basket_no))
            if sample_no is not None and sample_no>0 and sample_no <=Basket.NO_OF_SAMPLES_PER_PUCK:
                sample = self.getComponentByAddress(Pin.getSampleAddress(basket_no, sample_no))            
        except:
          pass
        self._setSelectedComponent(basket)
        self._setSelectedSample(sample)

    def _doSelect(self,component):
        """
        Selects a new component (basket or sample).
	Uses method >_directlyUpdateSelectedComponent< to actually search and select the corrected positions.

        :returns: None
        :rtype: None
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
        Scans the barcode of a single sample, puck or recursively even the complete sample changer.

        :returns: None
        :rtype: None
        """
        selected_basket = self.getSelectedComponent()
        if isinstance(component, Sample):            
            # scan a single sample
            if (selected_basket is None) or (selected_basket != component.getContainer()):
                self._doSelect(component)            
            selected=self.getSelectedSample()            
            # self._executeServerTask(self._scan_samples, [component.getIndex()+1,])
            basket = selected.getBasketNo()
            sample = selected.getVialNo()
            argin = [str(basket), str(sample)]
            self._executeServerTask(self._cmdScanSample, argin)
            self._updateSampleBarcode(component)
        elif isinstance(component, Container) and ( component.getType() == Basket.__TYPE__):
            # component is a basket
            if recursive:
                pass
            else:
                if (selected_basket is None) or (selected_basket != component):
                    self._doSelect(component)            
                # self._executeServerTask(self._scan_samples, (0,))                
                selected=self.getSelectedSample()            
                for sample_index in range(Basket.NO_OF_SAMPLES_PER_PUCK):
                    basket = selected.getBasketNo()
                    sample = sample_index+1
                    argin = [str(basket), str(sample)]
                    self._executeServerTask(self._cmdScanSample, argin)
        elif isinstance(component, Container) and ( component.getType() == SC3.__TYPE__):
            for basket in self.getComponents():
                self._doScan(basket, True)
    
    def isDeviceEnabled(self):
        return self._chnPowered.getValue()

    def _doLoad(self,sample=None):
        """
        Loads a sample on the diffractometer. Performs a simple put operation if the diffractometer is empty, and 
        a sample exchange (unmount of old + mount of new sample) if a sample is already mounted on the diffractometer.

        :returns: None
        :rtype: None
        """
        if not self.isDeviceEnabled():
            msg = "ISARA2 power is not enabled. Please switch on arm power before transferring samples."
            logging.getLogger("user_level_log").error(msg)
            raise Exception(msg)
            
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
        # argin = [TOOL_ID, str(basket), str(sample), "0", "0", "0", "0", "0"]
        argin = [str(basket), str(sample)]
            
        loadedsample = self.getLoadedSample()
        selectedsample = self.getSelectedSample()

        if self.hasLoadedSample():
            if selected==self.getLoadedSample():
                raise Exception("The sample " + str(self.getLoadedSample().getAddress()) + " is already loaded")
            else:
                self._executeServerTask(self._cmdChainedLoad, argin)
        else:
            self._executeServerTask(self._cmdLoad, argin)
            
    def _doChainedLoad(self, sample_to_unload=None, sample=None):
        return self._doLoad(sample)

    def _doUnload(self,sample_slot=None):
        """
        Unloads a sample from the diffractometer.

        :returns: None
        :rtype: None
        """
        if not self.isDeviceEnabled():
            msg = "ISARA2 power is not enabled. Please switch on arm power before transferring samples."
            logging.getLogger("user_level_log").error(msg)
            raise Exception(msg)
            
        if (sample_slot is not None):
            self._doSelect(sample_slot)
        # argin = [Isara2.TOOL_ID, "0", "0", "0", "0"]
        # self._executeServerTask(self._cmdUnload, argin)
        self._executeServerTask(self._cmdUnload)

    def clearBasketInfo(self, basket):
        pass

    ################################################################################

    def _doAbort(self):
        """
        Aborts a running trajectory on the sample changer.

        :returns: None
        :rtype: None
        """
        self._cmdAbort()            

    def _doReset(self):
        pass

    #########################           PRIVATE           #########################        

    def _updateOperationMode(self, value):
        self._scIsCharging = false

    def _executeServerTask(self, method, *args):
        """
        Executes a task on the ISARA Tango device server

        :returns: None
        :rtype: None
        """
        self._waitDeviceReady(3.0)
        task_id = method(*args)

        ret=None
        if task_id is None: #Reset
            while self._isDeviceBusy():
                gevent.sleep(0.1)
        else:
            # introduced wait because it takes some time before the attribute PathRunning is set
            # after launching a transfer
            time.sleep(2.0)
            while str(self._chnPathRunning.getValue()).lower() == 'true': 
                gevent.sleep(0.1)            
            ret = True
        return ret

    def _updateState(self):
        """
        Updates the state of the hardware object

        :returns: None
        :rtype: None
        """
        try:
          state = self._readState()
        except:
          state = SampleChangerState.Unknown

        if state == SampleChangerState.Moving and self._isDeviceBusy(self.getState()):
            #print "*** _updateState return"
            return          
        if self.hasLoadedSample() ^ self._chnSampleIsDetected.getValue():
            # go to Unknown state if a sample is detected on the gonio but not registered in the internal database
            # or registered but not on the gonio anymore
            state = SampleChangerState.Unknown
        elif self._chnPathRunning.getValue() and not (state in [SampleChangerState.Loading, SampleChangerState.Unloading]):
            state = SampleChangerState.Moving
        elif self._scIsCharging and not (state in [SampleChangerState.Alarm, SampleChangerState.Moving, SampleChangerState.Loading, SampleChangerState.Unloading]):
            state = SampleChangerState.Charging
        # print "*** _updateState: ", state
        self._setState(state)
       
    def _readState(self):
        """
        Read the state of the Tango DS and translate the state to the SampleChangerState Enum

        :returns: Sample changer state
        :rtype: GenericSampleChanger.SampleChangerState
        """
        state = self._chnState.getValue()
        # print "*** _readState1: ", state
        if state is not None:
            stateStr = str(state).upper()
        else:
            stateStr = ""
        # state = str(self._state.getValue() or "").upper()
        state_converter = { "ALARM": SampleChangerState.Alarm,
                            "ON": SampleChangerState.Ready,
                            "OFF": SampleChangerState.StandBy,
                            "FAULT": SampleChangerState.Fault,
                            "RUNNING": SampleChangerState.Moving }
        return state_converter.get(stateStr, SampleChangerState.Unknown)
                        
    def _isDeviceBusy(self, state=None):
        """
        Checks whether Sample changer HO is busy.

        :returns: True if the sample changer is busy
        :rtype: Bool
        """
        if state is None:
            state = self._readState()
        return state not in (SampleChangerState.Ready, SampleChangerState.Loaded, SampleChangerState.Alarm, 
                             SampleChangerState.Disabled, SampleChangerState.Fault, SampleChangerState.StandBy)

    def _isDeviceReady(self):
        """
        Checks whether Sample changer HO is ready.

        :returns: True if the sample changer is ready
        :rtype: Bool
        """
        state = self._readState()
        return state in (SampleChangerState.Ready, SampleChangerState.Charging, SampleChangerState.StandBy)              

    def _waitDeviceReady(self,timeout=None):
        """
        Waits until the samle changer HO is ready.

        :returns: None
        :rtype: None
        """

        with gevent.Timeout(timeout, Exception("Timeout waiting for device ready")):
            while not self._isDeviceReady():
                gevent.sleep(0.01)
            
    def _updateSelection(self):    
        """
        Updates the selected basket and sample. NOT USED ANYMORE FOR THE ISARA.
        Legacy method left from the implementation of the SC3 where the currently selected sample
        is always read directly from the SC3 Tango DS

        :returns: None
        :rtype: None
        """
        #import pdb; pdb.set_trace()
        basket=None
        sample=None
        # print "_updateSelection: saved selection: ", self._selected_basket, self._selected_sample
        try:
          basket_no = self._selected_basket
          if basket_no is not None and (basket_no > 0) and (basket_no <= Isara2.NO_OF_BASKETS):
            basket = self.getComponentByAddress(Basket.getBasketAddress(basket_no))
            sample_no = self._selected_sample
            if sample_no is not None and sample_no>0 and sample_no <=Basket.NO_OF_SAMPLES_PER_PUCK:
                sample = self.getComponentByAddress(Pin.getSampleAddress(basket_no, sample_no))            
        except:
          pass
        #if basket is not None and sample is not None:
        #    print "_updateSelection: basket: ", basket, basket.getIndex()
        #    print "_updateSelection: sample: ", sample, sample.getIndex()
        self._setSelectedComponent(basket)
        self._setSelectedSample(sample)

    def _updateLoadedSample(self):
        """
        Reads the currently mounted sample basket and pin indices from the ISARA Tango DS,
        translates the lid/sample notation into the basket/sample notation and marks the 
        respective sample as loaded.

        :returns: None
        :rtype: None
        """
        loadedSamplePuck = int(self._chnPuckLoadedSample.getValue())
        loadedSampleNum = int(self._chnNumLoadedSample.getValue())
        if loadedSamplePuck == -1 and loadedSampleNum == -1:
            basket = None
            samplePos = None
        else:
            basket = loadedSamplePuck
            samplePos = loadedSampleNum
 
        if basket is not None and samplePos is not None:
            new_sample = self.getComponentByAddress(Pin.getSampleAddress(basket, samplePos))
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
        Updates the barcode of >sample< in the local database after scanning with
        the barcode reader.

        :returns: None
        :rtype: None
        """
        # update information of recently scanned sample
        datamatrix = str(self._chnSampleBarcode.getValue())
        scanned = (len(datamatrix) != 0)
        if not scanned:    
           datamatrix = '----------'   
        sample._setInfo(sample.isPresent(), datamatrix, scanned)

    def _initSCContents(self):
        """
        Initializes the sample changer content with default values.

        :returns: None
        :rtype: None
        """
        # create temporary list with default basket information
        basket_list= [('', 4)] * Isara2.NO_OF_BASKETS
        # write the default basket information into permanent Basket objects 
        for basket_index in range(Isara2.NO_OF_BASKETS):            
            basket=self.getComponents()[basket_index]
            datamatrix = None
            present = scanned = False
            basket._setInfo(present, datamatrix, scanned)

        # create temporary list with default sample information and indices
        sample_list=[]
        for basket_index in range(Isara2.NO_OF_BASKETS):            
            for sample_index in range(Basket.NO_OF_SAMPLES_PER_PUCK):
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
        Updates the sample changer content. The state of the puck positions are
        read from the PuckPresence attribute in the ISARA Tango DS.
        The ISARA sample sample does not have an detection of each individual sample, so all
        samples are flagged as 'Present' if the respective puck is mounted.

        :returns: None
        :rtype: None
        """
        for basket_index in range(Isara2.NO_OF_BASKETS):            
            # get presence information from the device server
            newBasketPresence = getattr(self, "_chnPuckPresence").getValue()[basket_index]
            # get saved presence information from object's internal bookkeeping
            basket=self.getComponents()[basket_index]
           
            # check if the basket was newly mounted or removed from the dewar
            if newBasketPresence ^ basket.isPresent():
                # import pdb; pdb.set_trace()
                # a mounting action was detected ...
                if newBasketPresence:
                    # basket was mounted
                    present = True
                    scanned = False
                    datamatrix = None
                    basket._setInfo(present, datamatrix, scanned)
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
                        datamatrix = '          '   
                    else:
                        datamatrix = None
                    scanned = False
                    sample._setInfo(present, datamatrix, scanned)
                    # forget about any loaded state in newly mounted or removed basket)
                    loaded = has_been_loaded = False
                    sample._setLoaded(loaded, has_been_loaded)

def test():
    pass

if __name__ == '__main__':
    test()
