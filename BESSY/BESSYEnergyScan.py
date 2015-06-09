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
    def __init__(self, name, tunable_bl):
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

    def doChooch(self, elt, edge, scanArchiveFilePrefix, scanFilePrefix):
        symbol = "-".join((elt, edge))
        dateTime = time.strftime("%Y%m%d-%H%M%S")

        # build a detailed filename in the form prefix_1_Se-K_20141021-102440
        scanFilePrefix = "_".join((scanFilePrefix, symbol, dateTime))
        
        rawScanFile=os.path.extsep.join((scanFilePrefix, "raw"))
        scanFile=os.path.extsep.join((scanFilePrefix, "efs"))
        escan_png = os.path.extsep.join((scanFilePrefix, "png"))

        if not scanArchiveFilePrefix in (None, ""):
            scanArchiveFilePrefix = "_".join((scanArchiveFilePrefix, symbol))
            archiveRawScanFile=os.path.extsep.join((scanArchiveFilePrefix, "raw"))
            if not os.path.exists(os.path.dirname(scanArchiveFilePrefix)):
                os.makedirs(os.path.dirname(scanArchiveFilePrefix))

        raw_data_file = '/141dat/pxrdat/scans/today/d_scan_000.raw'
        try:
             scanData = self._readScanData(raw_data_file)
        except:
            self.storeEnergyScan()
            self.emit("energyScanFailed", ())
            return

        self._writeRawDataToDisk(rawScanFile, scanData)
        if not scanArchiveFilePrefix in (None, ""):
            shutil.copy(rawScanFile, archiveRawScanFile)
            self.energy_scan_parameters["scanFileFullPath"]=str(archiveRawScanFile)
        else:
            self.energy_scan_parameters["scanFileFullPath"]=str(rawScanFile)

        pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, chooch_graph_data = PyChooch.calc(scanData, elt, edge, scanFile)
        
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

        chooch_graph_x, chooch_graph_y1, chooch_graph_y2 = zip(*chooch_graph_data)
        chooch_graph_x = list(chooch_graph_x)
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

        if not scanArchiveFilePrefix in (None, ""):
            archiveEfsFile=os.path.extsep.join((scanArchiveFilePrefix, "efs"))
            try:
                shutil.copy(scanFile, archiveEfsFile)
            except:
                self.storeEnergyScan()

        logging.getLogger("HWR").info("<chooch> Saving png" )
        # prepare to save png files
        title = "%10s  %6s  %6s\n%10s  %6.2f  %6.2f\n%10s  %6.2f  %6.2f" % ("energy", "f'", "f''", pk, fpPeak, fppPeak, ip, fpInfl, fppInfl) 
        x_axis_title = ("%s\n%s" % (scanFile, title))
        self._writePngResultFile(escan_png, scanData, chooch_graph_data, x_axis_title) 

        if not scanArchiveFilePrefix in (None, ""):
            escan_archivepng = os.path.extsep.join((scanArchiveFilePrefix, "png")) 
            self.energy_scan_parameters["jpegChoochFileFullPath"]=str(escan_archivepng)
            logging.getLogger("HWR").info("Saving energy scan to archive directory for ISPyB : %s", escan_archivepng)
            shutil.copy(escan_png, escan_archivepng)
        else:
            self.energy_scan_parameters["jpegChoochFileFullPath"]=str(escan_png)

        self.energy_scan_parameters['endTime']=time.strftime("%Y-%m-%d %H:%M:%S")
        self.storeEnergyScan()

        logging.getLogger("HWR").info("<chooch> returning" )
        self.emit('chooch_finished', (pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, rm, chooch_graph_x, chooch_graph_y1, chooch_graph_y2, title))
        return pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, rm, chooch_graph_x, chooch_graph_y1, chooch_graph_y2, title

