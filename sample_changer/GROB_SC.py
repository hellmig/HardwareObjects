from .GenericSampleChanger import *
from .Cats90 import Pin

class BasketType:
    """
    Enumeration of basket type
    """
    Unknown = 0
    Spine = 1
    Unipuck = 2

    BASKET_TYPE_DESC = { Unknown: "Unknown",
                         Spine : "Spine",
                         Unipuck : "Unipuck"}
    @staticmethod
    def tostring(type):
        return BasketType.STATE_DESC.get(state, "Unknown")

class Basket(Container):
    __TYPE__ = "Puck"    
    NO_OF_SAMPLES_PER_PUCKS = 0

    def __init__(self,container,number):
        super(Basket, self).__init__(self.__TYPE__,container,Basket.getBasketAddress(number),True)
        for i in range(self.getNumberOfSamples()):
            slot = Pin(self,number,i+1)
            self._addComponent(slot)
                            
    @staticmethod
    def getBasketAddress(basket_number):
        return str(basket_number)

    def clearInfo(self):
	self.getContainer()._reset_basket_info(self.getIndex()+1)
        self.getContainer()._triggerInfoChangedEvent()

    def getNumberOfSamples(self):
        return self.NO_OF_SAMPLES_PER_PUCKS

class SpineBasket(Basket):
    NO_OF_SAMPLES_PER_PUCKS = 10
    __BASKET_TYPE__ = BasketType.Spine

    def __init__(self, container, number):
        super(SpineBasket, self).__init__(container, Basket.getBasketAddress(number))

    def getBasketType(self):
        return self.__BASKET_TYPE__

class UnipuckBasket(Basket):
    NO_OF_SAMPLES_PER_PUCKS = 16
    __BASKET_TYPE__ = BasketType.Unipuck

    def __init__(self, container, number):
        super(UnipuckBasket, self).__init__(container, Basket.getBasketAddress(number))

    def getBasketType(self):
        return self.__BASKET_TYPE__


class GROB_SC(SampleChanger):
    __TYPE__ = "GROB_SC"

    def __init__(self, *args, **kwargs):
        super(GROB_SC, self).__init__(self.__TYPE__,False, *args, **kwargs)

    def init(self):
        self._scIsCharging = None
        self._enableScanning = 0
        self._enableUnipuckDoubleTool = 0

        # attributs
        # Process I/O 
        for channel_name in ("_chnState", "_chnDoorIsLocked", "_chnSampleIsDetected","_chnSCTransfertStateIsOn","_chnMiniToolAnnealingStateIsOn","_chnMiniToolFluoStateIsOn","_chnSCDetectorIsBack","_chnArmPowerIsOn","_chnArmIsHome","_chnSCUnloadStateRequest","_chnSCLoadStateRequest","_chnSCArmIsOutOfGonioArea","_chnSCSampleMagnetControl","_chnMiniToolAnnealingRequest","_chnMiniToolWashingRequest","_chnMiniToolFluoRequest","_chnPathRunning"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
        # Dewar
        for channel_name in ("_chnCryoLN2Level","_chnCryoHighLevel","_chnCryoHighLevelAlarm","_chnCryoLowLevel","_chnCryoLowLevelAlarm","_chnCryoLN2FillingValve","_chnCryoGN2Valve1","_chnCryoGN2Valve2"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
        # Other
        for channel_name in ("_chnCollisionSensorOK","_chnCalibrationTool","_chnToolHeaterOnOff","_chnDewarHeaterOnOff"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
        # Robot's attributs
        for channel_name in ("_chnPowered","_chnPathRunning","_chnToolIdentifier","_chnSpeedRatio"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
        # Others attributs
        for channel_name in ("_chnLastError","_chnScanning","_chnCalibrating","_chnDetecting","_chnFluoScreenIsReady","_chnAnnealingToolIsReady","_chnLN2Regulating","_chnLN2Warming","_chnDewarMotorPosition","_chnDewarNumberOfPucks","_chnIsPuckDetectionUptodate"):
            setattr(self, channel_name, self.getChannelObject(channel_name))
        for channel_name in ("_chnLid1State","_chnLid2State"):
            setattr(self, channel_name, self.getChannelObject(channel_name))


        # 2017-05-18-bessy-mh: begin - connect update signals to local methods
        self._chnPathRunning.connectSignal("update", self._updateRunningState)
        self._chnPowered.connectSignal("update", self._updatePoweredState)
        self._chnLastError.connectSignal("update", self._updateMessage)
        self._chnLN2Regulating.connectSignal("update", self._updateRegulationState)
        self._chnLid1State.connectSignal("update", self._updateLid1State)
        self._chnLid2State.connectSignal("update", self._updateLid2State)
        # 2017-05-18-bessy-mh: end

        # commands
        for commande_name in ("_cmdLoad","_cmdUnload","_cmdGetMountedSample","_cmdResetMountedSample","_cmdScanSample","_cmdScanPuck","_cmdScanDewar","_cmdReadSampleBarcode","_cmdReadPuckSampleBarcodes","_cmdToolDrying","_cmdToolDryingLimit","_cmdToolDryingDuration","_cmdToolHeaterOn","_cmdToolHeaterOff","_cmdDewarHeaterOn","_cmdDewarHeaterOff"):
            setattr(self, commande_name, self.getCommandObject(commande_name))
        for commande_name in ("_cmdAnnealing","_cmdStopAnnealing","_cmdWashing","_cmdMountFluoScreen","_cmdUnmountFluoScreen"):
            setattr(self, commande_name, self.getCommandObject(commande_name))
        for commande_name in ("_cmdRegulOn","_cmdRegulOff","_cmdWarmOn","_cmdWarmOff","_cmdOpenLid","_cmdCloseLid","_cmdIsLidOpened","_cmdDewarRotation"):
            setattr(self, commande_name, self.getCommandObject(commande_name))
        for commande_name in ("_cmdPuckType","_cmdLaunchPuckDetection","_cmdPuckDetection","_cmdSampleDetection"):
            setattr(self, commande_name, self.getCommandObject(commande_name))
        for commande_name in ("_cmdLogin","_cmdLogout","_cmdAddLog"):
            setattr(self, commande_name, self.getCommandObject(commande_name))
        for commande_name in ("_cmdPowerOn","_cmdPowerOff","_cmdBackTraj","_cmdAbort","_cmdStop","_cmdRestart","_cmdReset","_cmdHome","_cmdSafe","_cmdMountTool","_cmdUnmountTool","_cmdOpenTool","_cmdCloseTool","_cmdAlarmAcknowledge","_cmdShuntACOn","_cmdShuntACOff","_cmdSystemErrorAcknowledge"):
            setattr(self, commande_name, self.getCommandObject(commande_name))

        # initialize the sample changer components
        nbPucks = self.numberOfPucks()
        for i in range (nbPucks):
            bType = self.puckType(i+1)
            if bType == BasketType.Spine:
                sbasket = SpineBasket(self, i+1)
                self._addComponent(sbasket)
            else:
                ubasket = UnipuckBasket(self, i+1)
                self._addComponent(ubasket)

        # self.firstStateChange = True
        SampleChanger.init(self)

    def readState(self):
        return self._readState() 

    def doorIsLocked(self):
        return self._chnDoorIsLocked.getValue()

    def sampleIsDetected(self):
        return self._chnSampleIsDetected.getValue()

    def miniToolAnnealingStateIsOn(self):
        return self._chnMiniToolAnnealingStateIsOn.getValue()

    def miniToolFluoStateIsOn(self):
        return self._chnMiniToolFluoStateIsOn.getValue()

    def detectorIsBack(self):
        return self._chnDetectorIsBack.getValue()

    def armPowerIsOn(self):
        return self._chnArmPowerIsOn.getValue()

    def armIsHome(self):
        return self._chnArmIsHome.getValue()

    def unloadStateRequest(self):
        return self._chnSCUnloadStateRequest.getValue()

    def loadStateRequest(self):
        return self._chnSCLoadStateRequest.getValue()

    def armIsOutOfGonioArea(self):
        return self._chnSCArmIsOutOfGonioArea.getValue()

    def sampleMagnetControl(self):
        return self._chnSCSampleMagnetControl.getValue()

    def miniToolAnnealingRequest(self):
        return self._chnMiniToolAnnealingRequest.getValue()

    def miniToolWashingRequest(self):
        return self._chnMiniToolWashingRequest.getValue()

    def miniToolFluoRequest(self):
        return self._chnMiniToolFluoRequest.getValue()

    def pathRunning(self):
        return self._chnPathRunning.getValue()

    def numberOfPucks(self):
        return self._chnDewarNumberOfPucks.getValue()

    def puckType(self, puckId):
        return self._cmdPuckType(puckId)

    def getBasketList(self):
        basket_list = []
        for basket in self.getComponents():
            if isinstance(basket, Basket):
                basket_list.append(basket)
        return basket_list

    def load(self, sample=None, wait=True):    
        """
        Load a sample. 
        """    
        sample = self._resolveComponent(sample)
        self.assertNotCharging()
        return self._executeTask(SampleChangerState.Loading,wait,self._doLoad,sample)     

    def hasLoadedSample(self):
        sample = self.getLoadedSample()
        return (sample is not None)

    def is_mounted_Sample(self, sample):
        lSample = self.getLoadedSample()
        return lSample == sample

    def resetLoadedSample(self):
        self._cmdResetMountedSample()

    def enableScanning(self):
        self._enableScanning = 1

    def disableScanning(self):
        self._enableScanning = 0

    def isScanningEnabled(self):
        return self._enableScanning==1

    def enableUnipuckDoubleTool(self):
        self._enableUnipuckDoubleTool = 1

    def disableUnipuckDoubleTool(self):
        self._enableUnipuckDoubleTool = 0

    def isUnipuckDoubleToolEnabled(self):
        return self._enableUnipuckDoubleTool==1

    def lastError(self):
        return self._chnLastError.getValue()

    def toolDrying(self, duration):
        return self._executeTask(SampleChangerState.Moving,True,self._doToolDrying,duration)

    def toolDryingLimit(self, toolId, limit) :
        argin = [toolId, limit]
        return self._cmdToolDryingLimit(argin)

    def toolDryingDuration(self, toolId, duration) :
        argin = [toolId, duration]
        return self._cmdToolDryingDuration(argin)

    def launchDetection(self):
        self._executeTask(SampleChangerState.Moving,True,self._doLaunchDetection,None)
        self._updateDetection()

    def updateDetection(self):
        self._updateDetection()

    def isDetectionUptodate(self):
        return self._chnIsPuckDetectionUptodate.getValue()

    def toolHeaterOn(self):
        self._cmdToolHeaterOn()

    def toolHeaterOff(self):
        self._cmdToolHeaterOff()

    def isToolHeaterOn(self):
        return self._chnToolHeaterOnOff.getValue()

    def dewarHeaterOn(self):
        self._cmdDewarHeaterOn()

    def dewarHeaterOff(self):
        self._cmdDewarHeaterOff()

    def isDewarHeaterOn(self):
        return self._chnDewarHeaterOnOff.getValue()

    def enableRegulation(self):
        self._cmdRegulOn()

    def disableRegulation(self):
        self._cmdRegulOff()

    def isRegulationEnabled(self):
        return self._chnLN2Regulating.getValue()

    def enableWarming(self):
        self._cmdWarmOn()

    def disableWarming(self):
        self._cmdWarmOff()

    def isWarmingEnabled(self):
        return self._chnLN2Warming.getValue()

    def openLid(self, lid):
        self._cmdOpenLid(lid)

    def closeLid(self, lid):
        self._cmdCloseLid(lid)

    def isLidOpened(self, lid):
        return self._cmdIsLidOpened(lid)

    def readCryoLevel(self):
        return self._chnCryoLN2Level.getValue()

    def readCryoHighLevel(self):
        return self._chnCryoHighLevel.getValue()

    def readCryoHighLevelAlarm(self):
        return self._chnCryoHighLevelAlarm.getValue()

    def readCryoLowLevel(self):
        return self._chnCryoLowLevel.getValue()

    def readCryoLowLevelAlarm(self):
        return self._chnCryoLowLevelAlarm.getValue()

    def readCryoLN2FillingValve(self):
        return self._chnCryoLN2FillingValve.getValue()

    def readCryoGN2Valve1(self):
        return self._chnCryoGN2Valve1.getValue()

    def readCryoGN2Valve2(self):
        return self._chnCryoGN2Valve2.getValue()

    def readDewarMotorPosition(self):
        return self._chnDewarMotorPosition.getValue()

    def doAnnealing(self, duration, number):
        self._executeTask(SampleChangerState.Moving,True,self._doAnnealing,duration, number)

    def stopAnnealing(self):
        self._executeTask(SampleChangerState.Moving,True,self._doStopAnnealing,None)

    def isAnnealingReady(self):
        return self._chnAnnealingToolIsReady.getValue()

    def doWashing(self):
        self._executeTask(SampleChangerState.Moving,True,self._doWashing,None)
        
    def doMountFluoScreen(self):
        self._executeTask(SampleChangerState.Moving,True,self._doMountFluoScreen,None)

    def doUnmountFluoScreen(self):
        self._executeTask(SampleChangerState.Moving,True,self._doUnmountFluoScreen,None)

    def isFluoScreenReady(self):
        return self._chnFluoScreenIsReady.getValue()

    def backTraj(self):
        self._executeTask(SampleChangerState.Moving,True,self._doBackTraj,None)
        
    def safeTraj(self):
        self._executeTask(SampleChangerState.Moving,True,self._doSafeTraj,None)

    def stop(self):
        self._cmdStop()

    def reset(self):
        self._cmdReset()

    def restart(self):
        self._cmdRestart()

    def abort(self):
        self._cmdAbort()

    def home(self):
        self._executeTask(SampleChangerState.Moving,True,self._doHome,None)
        
    def mountTool(self, toolId):
        self._executeTask(SampleChangerState.Moving,True,self._doMountTool,str(toolId))

    def unmountTool(self):
        self._executeTask(SampleChangerState.Moving,True,self._doUnmountTool,None)

    def openTool(self, gripperId):
        return self._cmdOpenTool(gripperId)

    def closeTool(self, gripperId):
        return self._cmdCloseTool(gripperId)

    def alarmAcknowledge(self):
        self._cmdAlarmAcknowledge()

    def shuntACOn(self):
        self._cmdShuntACOn()

    def shuntACOff(self):
        self._cmdShuntACOff()

    def systemErrorAcknowledge(self):
        self._cmdSystemErrorAcknowledge()

    #########################           ATTRIBUTS           #########################


    def _readState(self):
        """
        Read the state of the Tango DS and translate the state to the SampleChangerState Enum

        :returns: Sample changer state
        :rtype: GenericSampleChanger.SampleChangerState
        """
        state = self._chnState.getValue()
        # print state
        if state is not None:
            stateStr = str(state).upper()
        else:
            stateStr = ""
        #state = str(self._state.getValue() or "").upper()
        state_converter = { "ALARM": SampleChangerState.Alarm,
                            "ON": SampleChangerState.Ready,
                            "RUNNING": SampleChangerState.Moving,
                            "MOVING": SampleChangerState.Moving,
                            "FAULT": SampleChangerState.Fault}
        return state_converter.get(stateStr, SampleChangerState.Unknown)

    #########################           TASKS           #########################

    def _doUpdateInfo(self):       
        """
        Updates the sample changers status: mounted pucks, state, currently loaded sample

        :returns: None
        :rtype: None
        """
        #if self.firstStateChange:
        #    self.firstStateChange = False
        #    state = self._readState()
        #    self._setState(state, SampleChangerState.tostring(state))
            
        self._updateDetection()
	# A better solution could be to connect a callback to SampleIsDetected
	self._updateLoadedSample()
        self._updateState()  
	
    def _doAbort(self):
        print "_doAbort"

    def _doChangeMode(self):
        print "_doChangeMode"

 
    def _doSelect(self,component):
        """
        Selects a new component (basket or sample).
        :returns: None
        :rtype: None
        """
        if isinstance(component, Sample):
	    selected_basket_no = component.getBasketNo()
            selected_sample_no = component.getIndex()+1
            self._setSelectedComponent(self.getBasketList()[selected_basket_no-1])
            self._setSelectedSample(component)
        elif isinstance(component, Container) and ( component.getType() == Basket.__TYPE__):
            selected_basket_no = component.getIndex()+1
            self._setSelectedComponent(component)
            self._setSelectedSample(None)
        return 0

    def _doScan(self,component,recursive):
        """
        Scans the barcode of a single sample, puck or recursively even the complete sample changer.

        :returns: None
        :rtype: None
        """
        selected_basket = self.getSelectedComponent()
        doubleTool = self._enableUnipuckDoubleTool #enough as long as double spine tool is not used
        if isinstance(component, Sample): 
            # scan a single sample
            if (selected_basket is None) or (selected_basket != component.getContainer()):
                self._doSelect(component)            
            selected=self.getSelectedSample()            
            # calculates GROB specific puck/sample number
            puck = selected.getBasketNo()
            sample = selected.getVialNo()
            print puck, sample
            argin = [str(doubleTool), str(puck-1), str(sample-1)]
            self._executeServerTask(self._cmdScanSample, argin)
            self._updateSampleBarcode(selected)
        elif isinstance(component, Container) and ( component.getType() == Basket.__TYPE__):
            print "*** Scan Puck "
            # component is a basket
            if (selected_basket is None) or (selected_basket != component):
                self._doSelect(component)            
            selected=self.getSelectedComponent()            
            puck = selected.getIndex()+1
            print puck
            argin = [str(doubleTool), str(puck-1)]
            self._executeServerTask(self._cmdScanPuck, argin)
            self._updatePuckSamplesBarcodes(selected)
        elif isinstance(component, Container) and ( component.getType() == SC3.__TYPE__):
            print "*** Scan Dewar "
            argin = [str(doubleTool)]
            self._executeServerTask(self._cmdDewar, argin)
            self._updateDewarBarcodes()

    def _updateSampleBarcode(self, sample):
        """
        Updates the barcode of >sample< in the local database after scanning with
        the barcode reader.

        :returns: None
        :rtype: None
        """
        # update information of recently scanned sample
        puckId = sample.getBasketNo()
        sampleId = sample.getVialNo()
        argin = [str(puckId-1), str(sampleId-1)]
        datamatrix = str(self._cmdReadSampleBarcode(argin))
        scanned = (len(datamatrix) != 0)
        if not scanned:    
           # datamatrix = '----------'   
           datamatrix = None
        # state = sample.isPresent()
        # print 'before', puckId, sampleId, state
        sample._setInfo(sample.isPresent(), datamatrix, scanned)
        # print 'after', puckId, sampleId, sample.isPresent()

    def _updatePuckSamplesBarcodes(self, basket):
        """
        Updates the barcodes of all samples of a <basket> in the local database after scanning with
        the barcode reader.

        :returns: None
        :rtype: None
        """
        # update information of recently scanned sample
        puckId = basket.getIndex()
        argout = self._cmdReadPuckSampleBarcodes(str(puckId))
        samples = basket.getComponents()
        for i in range(len(samples)):
            datamatrix = argout[i]
            scanned = (len(datamatrix) != 0)
            if not scanned:    
                # datamatrix = "----------"   
                datamatrix = None
            samples[i]._setInfo(samples[i].isPresent(), datamatrix, scanned)

    def _updateDewarBarcodes(self):
        """
        Updates the barcode of all samples of the Dewar in the local database after scanning with
        the barcode reader.

        :returns: None
        :rtype: None
        """
        # update information of recently scanned sample
        basketList = self.getBasketList()
        for i in range(len(basketList)):
            self._updatePuckSamplesBarcodes(basketList[i])

    def _doLoad(self, sample=None):
        selected = self.getSelectedSample()
        doubleTool = self._enableUnipuckDoubleTool #enough as long as double spine tool is not used
        scan = self._enableScanning
        if sample is not None:
            if sample != selected:
                self._doSelect(sample)
                selected=self.getSelectedSample()
        else:
            if selected is not None:
                sample = selected
            else:
                raise Exception("No sample selected")
        # calculates GROB specific puck/sample number
        puck = selected.getBasketNo()
        sample = selected.getVialNo()
        print puck, sample, scan
        argin = [str(doubleTool), str(puck-1), str(sample-1), str(scan)]
        ret = self._executeServerTask(self._cmdLoad, argin)
        if scan==1:
            self._updateSampleBarcode(selected)
	self._updateLoadedSample()
        return ret

    def _doReset(self):
        ret = self._cmdSystemErrorAcknowledge()
        return ret

    def _doUnload(self,sample_slot=None):
        doubleTool = self._enableUnipuckDoubleTool #enough as long as double spine tool is not used
        argin = [str(doubleTool)]
        ret = self._executeServerTask(self._cmdUnload,argin)
	self._updateLoadedSample()

    def _doLaunchDetection(self, argin):
        ret = self._executeServerTask(self._cmdLaunchPuckDetection, None)

    def _doAnnealing(self, duration, number):
        argin = [duration, number]
        ret = self._executeServerTask(self._cmdAnnealing, argin)

    def _doStopAnnealing(self, argin):
        ret = self._executeServerTask(self._cmdStopAnnealing, None)
        
    def _doWashing(self, argin):
        ret = self._executeServerTask(self._cmdWashing, None)

    def _doMountFluoScreen(self, argin):
        ret = self._executeServerTask(self._cmdMountFluoScreen, None)

    def _doUnmountFluoScreen(self, argin):
        ret = self._executeServerTask(self._cmdUnmountFluoScreen, None)

    def _updateDetection(self):
        """
        Updates the presence status of all pucks and samples of the Dewar in the local database 
        """
        argout = self._cmdPuckDetection()
        basketList = self.getBasketList()
        for i in range(len(basketList)):
            presence = (argout[i]==1)
            basket = basketList[i]
            basket._setInfo(presence, basket.getID(), basket.isScanned)
            if presence:
                sampleList=basket.getComponents()
                argout2 = self._cmdSampleDetection(basket.getIndex())
                for j in range(len(sampleList)):
                    sample = sampleList[j]
                    sample._setInfo((argout2[j]==1),sample.getID(),sample.isScanned())
                    self._updateSampleBarcode(sample)

    def _updateLoadedSample(self):
        """
        Reads the currently mounted sample basket and pin indices from the CATS Tango DS,
        translates the lid/sample notation into the basket/sample notation and marks the 
        respective sample as loaded.

        :returns: None
        :rtype: None
        """

        argout = self._cmdGetMountedSample()
        if (argout[0]< 0):
            new_sample = None
        else:
            puck_id = argout[0]
            sample_id = argout[1]
            new_sample = self.getComponents()[puck_id].getComponents()[sample_id]
	
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
  
    def _doBackTraj(self, argin):
        ret = self._executeServerTask(self._cmdBackTraj, None)
             
    def _doSafeTraj(self, argin):
        ret = self._executeServerTask(self._cmdSafe, None)

    def _doHome(self, argin):
        ret = self._executeServerTask(self._cmdHome, None)
    
    def _doMountTool(self, argin):
        ret = self._executeServerTask(self._cmdMountTool, argin)

    def _doUnmountTool(self, argin):
        ret = self._executeServerTask(self._cmdUnmountTool, None)

    def _doToolDrying(self, argin):
        ret = self._executeServerTask(self._cmdToolDrying, argin)

    def _updateState(self):
        """
        Updates the state of the hardware object

        :returns: None
        :rtype: None
        """
        try:
	  #self.state = self._readState()
          self._setState(self._readState())
        except:
          self.state = SampleChangerState.Unknown
        # print self.state, type(self.state)
        #self.status = SampleChangerState.tostring(self.state)
	self._setState(self.state) #, self.status)
        # print self.state, type(self.state), self.status
        

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
        return state in (SampleChangerState.Ready, SampleChangerState.Charging)              

    def _waitDeviceReady(self,timeout=None):
        """
        Waits until the samle changer HO is ready.

        :returns: None
        :rtype: None
        """

        with gevent.Timeout(timeout, Exception("Timeout waiting for device ready")):
            while not self._isDeviceReady():
                gevent.sleep(0.01)
 
    #########################           PRIVATE           #########################        

    # ------------ SIGNALS ------------
    def _updateRunningState(self, value):
        self.emit('runningStateChanged', (value, ))

    def _updatePoweredState(self, value):
        self.emit('powerStateChanged', (value, ))
    
    def _updateMessage(self, value):
        self.emit('messageChanged', (value, ))

    def _updateRegulationState(self, value):
        self.emit('regulationStateChanged', (value, ))

    def _updateLid1State(self, value):
        self.emit('lid1StateChanged', (value, ))

    def _updateLid2State(self, value):
        self.emit('lid2StateChanged', (value, ))

    def connectNotify(self, signal):
        if signal == 'runningStateChanged':
            self.emit('runningStateChanged', self._chnPathRunning.getValue())
        elif signal == 'powerStateChanged':
            self.emit('powerStateChanged', self._chnPowered.getValue())
        elif signal == 'messageChanged':
            self.emit('messageChanged', self._chnLastError.getValue())
        elif signal == 'regulationStateChanged':
            self.emit('regulationStateChanged', self._chnLN2Regulating.getValue())
        elif signal == 'lid1StateChanged':
            self.emit('lid1StateChanged', self._chnLid1State.getValue())
        elif signal == 'lid2StateChanged':
            self.emit('lid2StateChanged', self._chnLid2State.getValue())
        else:
            logging.getLogger().info ("connectNotify " + str(signal))

    # ------------ SIGNALS ------------

    def _executeServerTask(self, method, *args):
        """
        Executes a task on the GROB Tango device server

        :returns: None
        :rtype: None
        """
        self._waitDeviceReady(3.0)
        task_id = method(*args)
        print "GROB._executeServerTask", task_id
        ret=True
        if task_id is None: #Reset
            while self._isDeviceBusy():
                gevent.sleep(0.1)
            ret = False
        else:
            # introduced wait because it takes some time before the attribute PathRunning is set
            # after launching a transfer
            time.sleep(2.0)
            self._updateState()
            while self.state == SampleChangerState.Moving:
                gevent.sleep(0.5)            
            self._updateState()
            print self.state
            if self.state == SampleChangerState.Fault:
                err = self._chnLastError.getValue()
                print err
                ret = False
        return ret

    def _doPowerState(self, state=False):
        """
        Switch on CATS power if >state< == True, power off otherwise

        :returns: None
        :rtype: None
        """
        if state:
            self._cmdPowerOn()
        else:
            self._cmdPowerOff()

    def _doEnableRegulation(self):
        """
        Switch on CATS regulation

        :returns: None
        :rtype: None
        """
        self._cmdRegulOn()

    def _doDisableRegulation(self):
        """
        Switch off CATS regulation

        :returns: None
        :rtype: None
        """
        self._cmdRegulOff()

    def _doLid1State(self, state = True):
        """
        Opens lid 1 if >state< == True, closes the lid otherwise

        :returns: None
        :rtype: None
        """
        argin = 1
        if state:
            self._executeServerTask(self._cmdOpenLid, argin)
        else:
            self._executeServerTask(self._cmdCloseLid, argin)

    def _doLid2State(self, state = True):
        """
        Opens lid 2 if >state< == True, closes the lid otherwise

        :returns: None
        :rtype: None
        """
        argin = 2
        if state:
            self._executeServerTask(self._cmdOpenLid, argin)
        else:
            self._executeServerTask(self._cmdCloseLid, argin)
