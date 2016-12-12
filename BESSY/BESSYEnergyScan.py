from HardwareRepository.BaseHardwareObjects import HardwareObject
from AbstractEnergyScan import *
from gevent.event import AsyncResult
import logging
import time
import os
import shutil
import httplib
import math
import PyChooch
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


class FixedEnergy:

    @task
    def get_energy(self):
        return self._tunable_bl.energy_obj.getPosition()


class TunableEnergy:

    @task
    def get_energy(self):
        return self._tunable_bl.energy_obj.getCurrentEnergy()

    @task
    def move_energy(self, energy):
        return self._tunable_bl.energy_obj.startMoveEnergy(energy, wait=True)

    
class BESSYEnergyScan(AbstractEnergyScan, HardwareObject):
   
    # RAW_DATA_FILE_PATH must be overwritten by the beamline-specific
    # implementions in BESSY141EnergyScan/BESSY142EnergyScan
    RAW_DATA_FILE_PATH = "/path/to/data/file"

    def __init__(self, name, tunable_bl):
        # print "BESSYEnergyScan.__init__"
        AbstractEnergyScan.__init__(self)
        HardwareObject.__init__(self, name)
        self._tunable_bl = tunable_bl

    def execute_command(self, command_name, *args, **kwargs): 
        wait = kwargs.get("wait", True)
        cmd_obj = self.getCommandObject(command_name)
        return cmd_obj(*args, wait=wait)

    def init(self):
        self.energy_obj =  self.getObjectByRole("energy")
        #self.safety_shutter = self.getObjectByRole("safety_shutter")
        # self.beamsize = self.getObjectByRole("beamsize")
        #self.transmission = self.getObjectByRole("transmission")
        self.ready_event = gevent.event.Event()
        #self.dbConnection=self.getObjectByRole("dbserver")
        self.dbConnection = None
        if self.dbConnection is None:
            logging.getLogger("HWR").warning('EnergyScan: you should specify the database hardware object')
        self.scanInfo=None
        self.scanData = None
        self._tunable_bl.energy_obj = self.energy_obj

        self._xf_elem = self.getChannelObject("xf_elem_table")
        self._am_elem = self.getChannelObject("am_elem_table")

    def isConnected(self):
        return True

    def _get_spec_xfe_pars(self, element, edge):

        xf_table = self._xf_elem.getValue()
        am_table = self._am_elem.getValue()

        xf_elem = xf_table[element]
        am_elem = am_table[element]

        xfdat = map(float, xf_elem.split()[2:])
        amdat = map(float, am_elem.split()[4:])

        edge_energy = amdat[0]

        static_pars = {}
        edge_energy /= 1000
        static_pars["edgeEnergy"] = edge_energy
        static_pars["startEnergy"] = edge_energy - 0.05
        static_pars["endEnergy"] = edge_energy + 0.05
        static_pars["remoteEnergy"] = edge_energy + 1
        static_pars["eroi_min"] = xfdat[0]
        static_pars["eroi_max"] = xfdat[1]
        
        return static_pars
    
    @task
    def get_static_parameters(self, element, edge):

        pars = self._get_spec_xfe_pars(element, edge)
        
        offset_keV = self.getProperty("offset_keV")
        pars["startEnergy"] += offset_keV
        pars["endEnergy"] += offset_keV

        return pars

    @task
    def open_safety_shutter(self):
        pass

    @task
    def close_safety_shutter(self):
        pass

    @task
    def escan_prepare(self):
        #self.execute_command("presetScan")
        #bsX = self.beamsize.getCurrentPositionName()
        #bsY = bsX
        #self.energy_scan_parameters["beamSizeHorizontal"] = bsX
        #self.energy_scan_parameters["beamSizeVertical"]=bsY
        pass

    @task
    def escan_postscan(self):
        #self.execute_command("cleanScan")
        pass
        
    @task
    def escan_cleanup(self):
        self.close_fast_shutter()
        self.close_safety_shutter()
        #self.execute_command("cleanScan")
        self.emit("energyScanFailed", ())
        self.ready_event.set()

    @task
    def close_fast_shutter(self):
        pass

    @task
    def open_fast_shutter(self):
        pass

    @task
    def move_energy(self, energy):
        #return self.energy_obj.startMoveEnergy(energy, wait=True)
        pass

    # Elements commands
    def getElements(self):
        elements=[]
        try:
            for el in self["elements"]:
                elements.append({"symbol":el.symbol, "energy":el.energy})
        except IndexError:
            pass

        return elements

    def get_scan_data(self):
        """
        Descript. : returns energy scan data.
                    List contains tuples of (energy, counts)
        """
        return self.scanData 

    def storeEnergyScan(self):
        pass

    def _readScanData(self, raw_data_file):
        
        scanData = []
        raw_file = open(raw_data_file, 'r')
        textbuffer = raw_file.readlines()
        raw_file.close()

        for line in textbuffer[2:]:
            # split columns of raw energy scan data by any combination of whitespace
            (x, y) = line.split()
            x = float(x.strip())
            y = float(y.strip())
            #x = x < 1000 and x*1000.0 or x
            scanData.append((x, y))
            
        return scanData
    
    def _writeRawDataToDisk(self, output_filename, scanData):

        try:
            f=open(output_filename, "w")
        except:
            logging.getLogger("HWR").warning("could not create raw scan files")
            self.storeEnergyScan()
            return

        for datatuple in scanData:
            f.write("%f,%f\r\n" % datatuple)
        f.close()
        return

    def _writePngResultFile(self, escan_png, scanData, chooch_graph_data, x_axis_title):

        chooch_graph_x, chooch_graph_y1, chooch_graph_y2 = zip(*chooch_graph_data)
        chooch_graph_x = list(chooch_graph_x)
        for i in range(len(chooch_graph_x)):
          chooch_graph_x[i]=chooch_graph_x[i]/1000.0

        # prepare to save png files
        #title="%10s  %6s  %6s\n%10s  %6.2f  %6.2f\n%10s  %6.2f  %6.2f" % ("energy", "f'", "f''", pk, fpPeak, fppPeak, ip, fpInfl, fppInfl) 
        fig=Figure(figsize=(15, 11))
        ax=fig.add_subplot(211)
        #ax.set_title("%s\n%s" % (scanFile, title))
        ax.set_title(x_axis_title)
        ax.grid(True)
        ax.plot(*(zip(*scanData)), **{"color":'black'})
        ax.set_xlabel("Energy")
        ax.set_ylabel("MCA counts")
        ax2=fig.add_subplot(212)
        ax2.grid(True)
        ax2.set_xlabel("Energy")
        ax2.set_ylabel("")
        handles = []
        handles.append(ax2.plot(chooch_graph_x, chooch_graph_y1, color='blue'))
        handles.append(ax2.plot(chooch_graph_x, chooch_graph_y2, color='red'))
        canvas=FigureCanvasAgg(fig)

        try:
            logging.getLogger("HWR").info("Rendering energy scan and Chooch graphs to PNG file : %s", escan_png)
            canvas.print_figure(escan_png, dpi=80)
        except:
            logging.getLogger("HWR").exception("could not print figure")
        return

    def doChooch(self, elt, edge, scan_directory, archive_directory, prefix):
        # from qt4_debug import *
        # bkpoint()
        symbol = "-".join((elt, edge))
        dateTime = time.strftime("%Y%m%d-%H%M%S")

        # build a detailed filename in the form prefix_1_Se-K_20141021-102440
        prefix = "_".join((prefix, symbol, dateTime))

        scan_file_prefix = os.path.join(scan_directory, prefix) 
        # don't include support for archive directory in our implementation
        archive_scan_file_prefix = None

        scan_file_raw_filename = os.path.extsep.join((scan_file_prefix, "raw"))
        scan_file_efs_filename = os.path.extsep.join((scan_file_prefix, "efs"))
        scan_file_png_filename = os.path.extsep.join((scan_file_prefix, "png"))

        # raw_data_file = '/142dat/pxrdat/scans/today/d_scan_000.raw'
        try:
             self.scanData = self._readScanData(self.RAW_DATA_FILE_PATH)
        except:
            self.storeEnergyScan()
            self.emit("energyScanFailed", ())
            return

        self._writeRawDataToDisk(scan_file_raw_filename, self.scanData)
        self.energy_scan_parameters["scanFileFullPath"]=str(scan_file_raw_filename)

        pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, chooch_graph_data = PyChooch.calc(self.scanData, elt, edge, scan_file_efs_filename)
	rm=(pk+30)/1000.0
	pk=pk/1000.0
	savpk = pk
	ip=ip/1000.0
	comm = ""

        self.energy_scan_parameters["peakEnergy"]=pk
        self.energy_scan_parameters["inflectionEnergy"]=ip
        self.energy_scan_parameters["remoteEnergy"]=rm
        self.energy_scan_parameters["peakFPrime"]=fpPeak
        self.energy_scan_parameters["peakFDoublePrime"]=fppPeak
        self.energy_scan_parameters["inflectionFPrime"]=fpInfl
        self.energy_scan_parameters["inflectionFDoublePrime"]=fppInfl
        self.energy_scan_parameters["comments"] = comm

        # 2016-04-11-bessy-mh - begin
        # the unzipping of the result list >chooch_graph_data< produces a RuntimeError exception while executing the list operation
        # for unknown reason on our exp141b Debian Wheezy installation
        # The issue seems to be independent of the energy-scan input data and can also be seen with the PyChooch example scan but the 
        # reason is not understood yet
        # As a workaround the lists are processed individually with added exception checking which "solves" the problem
        # chooch_graph_x, chooch_graph_y1, chooch_graph_y2 = zip(*chooch_graph_data)
        try:
          chooch_graph_x  = (x  for x, y1, y2 in chooch_graph_data)
          chooch_graph_y1 = (y1 for x, y1, y2 in chooch_graph_data)
          chooch_graph_y2 = (y2 for x, y1, y2 in chooch_graph_data)
        except RuntimeError:
	  pass
        # 2016-04-11-bessy-mh - end
        chooch_graph_x = list(chooch_graph_x)
        chooch_graph_y1 = list(chooch_graph_y1)
        chooch_graph_y2 = list(chooch_graph_y2)
        for i in range(len(chooch_graph_x)):
          chooch_graph_x[i]=chooch_graph_x[i]/1000.0

        self.thEdge = self.energy_scan_parameters['edgeEnergy']
        logging.getLogger("HWR").info("th. Edge %s ; chooch results are pk=%f, ip=%f, rm=%f" % (self.thEdge, pk,ip,rm))

        #should be better, but OK for time being
        self.thEdgeThreshold = 0.01
        if math.fabs(self.thEdge - ip) > self.thEdgeThreshold:
            pk = 0
            ip = 0
            rm = self.thEdge + 0.03
            comm = 'Calculated peak (%f) is more that 10eV away from the theoretical value (%f). Please check your scan' % (savpk, self.thEdge)
   
            logging.getLogger("HWR").warning('EnergyScan: calculated peak (%f) is more that 20eV %s the theoretical value (%f). Please check your scan and choose the energies manually' % (savpk, (self.thEdge - ip) > 0.02 and "below" or "above", self.thEdge))

        logging.getLogger("HWR").info("<chooch> Saving png" )
        # prepare to save png files
        title = "%10s  %6s  %6s\n%10s  %6.2f  %6.2f\n%10s  %6.2f  %6.2f" % ("energy", "f'", "f''", pk, fpPeak, fppPeak, ip, fpInfl, fppInfl) 
        x_axis_title = ("%s\n%s" % (scan_file_raw_filename, title))
        self._writePngResultFile(scan_file_png_filename, self.scanData, chooch_graph_data, x_axis_title) 

        self.energy_scan_parameters["jpegChoochFileFullPath"]=str(scan_file_png_filename)

        self.energy_scan_parameters['endTime']=time.strftime("%Y-%m-%d %H:%M:%S")
        self.storeEnergyScan()

        logging.getLogger("HWR").info("<chooch> returning" )
        self.emit('chooch_finished', (pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, rm, chooch_graph_x, chooch_graph_y1, chooch_graph_y2, title))
        return pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, rm, chooch_graph_x, chooch_graph_y1, chooch_graph_y2, title

    def startEnergyScan(self,element,edge,directory,prefix,session_id=None,blsample_id=None):

        self.emit('energyScanStarted', ())
        STATICPARS_DICT = {}
        #Set the energy from the element and edge parameters
        STATICPARS_DICT = self.get_static_parameters(element,edge)
        
        self.energy_scan_parameters = STATICPARS_DICT
        self.energy_scan_parameters["element"] = element
        self.energy_scan_parameters["edge"] = edge
        self.energy_scan_parameters["directory"] = directory
        #create the directory if needed
        if not os.path.exists(directory):
             os.makedirs(directory)
        self.energy_scan_parameters["prefix"]=prefix
        if session_id is not None:
            self.energy_scan_parameters["sessionId"] = session_id
            self.energy_scan_parameters["blSampleId"] = blsample_id
            self.energy_scan_parameters['startTime']=time.strftime("%Y-%m-%d %H:%M:%S")

        with error_cleanup(self.escan_cleanup):
            self.escan_prepare()
            self.energy_scan_hook(self.energy_scan_parameters)
            self.open_safety_shutter(timeout=10)
            self.choose_attenuation()
            self.close_fast_shutter()
            logging.getLogger("HWR").debug("Doing the scan, please wait...")
            self.execute_energy_scan(self.energy_scan_parameters)
            self.escan_postscan()
            
        self.close_fast_shutter()
        self.close_safety_shutter(timeout=10)
        #send finish sucessfully signal to the brick
        self.emit('energyScanFinished', (self.energy_scan_parameters,))
        self.ready_event.set()
