import time
import urllib


<<<<<<< HEAD
def getImage(barcode, inspection,row, col, shelf):
    #print (barcode, inspection,row, col, shelf)
    url = "https://embl.fr/htxlab/index.php?option=com_getbarcodextalinfos&task=getImage&format=raw&barcode=%s&inspection=%d&row=%s&column=%d&shelf=%d" %  (barcode, inspection,row, col, shelf)    
=======
import xml.etree.cElementTree as et

def getImage(url):
>>>>>>> origin/master
    f = urllib.urlopen(url)           
    img=f.read() 
    return img

<<<<<<< HEAD
def getProcessingPlanXML(barcode):
    #url = "https://embl.fr/htxlab/index.php?option=com_getbarcodextalinfos&task=getBarcodeXtalInfos&barcode=%s" % barcode
    #Crims V3
    url = "https://embl.fr/htxlabj3/index.php?option=com_getbarcodextalinfos&task=getBarcodeXtalInfos&format=xml&barcode=%s" % barcode
    #print "Opening URL: " + url
    f = urllib.urlopen(url)        
    #print "Reading: " + barcode
    xml = f.read()  
    #print "Received: " + xml
    return xml


=======
>>>>>>> origin/master
class Xtal:
    def __init__(self, *args):
        self.CrystalUUID=""
        self.PinID=""
        self.Login=""
        self.Sample=""
        self.Column=0
        self.idSample=0
        self.idTrial=0
        self.Row=""
        self.Shelf=0
        self.Comments=""
        self.offsetX=0.0
        self.offsetY=0.0
        self.IMG_URL=""
        self.ImageRotation=0.0
        self.SUMMARY_URL=""
        
<<<<<<< HEAD
        
=======
>>>>>>> origin/master
    def getAddress(self):
        return "%s%02d-%d" % (self.Row,self.Column,self.Shelf)

    def getImage(self):
<<<<<<< HEAD
        if (len(self.IMG_URL)==0):
            return None
        if (self.IMG_URL.startswith("http://")):
           self.IMG_URL = "https://" + self.IMG_URL[7];
        #print "Fetching: " + self.IMG_URL
        f = urllib.urlopen(self.IMG_URL)           
        
        img=f.read() 
        return img
=======
        if len(self.IMG_URL) > 0:
            try:
               if self.IMG_URL.startswith("http://"):
                   self.IMG_URL = "https://" + self.IMG_URL[7];
               image_string = urllib.urlopen(self.IMG_URL).read()           
               return image_string
            except:
               return 
>>>>>>> origin/master

    def getSummaryURL(self):
        if (len(self.SUMMARY_URL)==0):
            return None
        return self.SUMMARY_URL
        
class Plate:
    def __init__(self, *args):
        self.Barcode=""
        self.PlateType=""
        self.Xtal=[]

class ProcessingPlan:
    def __init__(self, *args):
        self.Plate=Plate()
 
<<<<<<< HEAD
def getProcessingPlan(barcode):
    try:    
        sxml = getProcessingPlanXML(barcode)
 
        import xml.etree.cElementTree as et
        tree=et.fromstring(sxml)
=======
def getProcessingPlan(barcode, crims_url):
    try: 
        url = crims_url + "/htxlab/index.php?option=com_crimswebservices" + \
           "&format=raw&task=getbarcodextalinfos&barcode=%s&action=insitu" % barcode
        f = urllib.urlopen(url)
        xml = f.read()

        import xml.etree.cElementTree as et
        tree=et.fromstring(xml)
>>>>>>> origin/master

        pp=ProcessingPlan()
        plate = tree.findall("Plate")[0]

        pp.Plate.Barcode = plate.find("Barcode").text
        pp.Plate.PlateType = plate.find("PlateType").text

        for x in plate.findall("Xtal"):
            xtal=Xtal()
            xtal.CrystalUUID=x.find("CrystalUUID").text
<<<<<<< HEAD
            xtal.PinID=x.find("Label").text
            xtal.Login=x.find("Login").text
            xtal.Sample=x.find("Sample").text
            xtal.Column=int(x.find("Column").text)
            xtal.idSample=int(x.find("idSample").text)
            xtal.idTrial=int(x.find("idTrial").text)
            xtal.Row=x.find("Row").text
            xtal.Shelf=int(x.find("Shelf").text)
            xtal.Comments=x.find("Comments").text
            xtal.offsetX=float(x.find("offsetX").text)
            xtal.offsetY=float(x.find("offsetY").text)
            xtal.IMG_URL=x.find("IMG_URL").text
            xtal.ImageRotation=float(x.find("ImageRotation").text)
            xtal.SUMMARY_URL=x.find("SUMMARY_URL").text
            pp.Plate.Xtal.append(xtal)
        return pp
    except:
        return None




if __name__ == "__main__":
    pp= getProcessingPlan("JZ005209")
    img=getImage("JZ005209",1,'C',12,1)
    print pp
    print pp.Plate
    
    
        
        
    
        
=======
            xtal.Label = x.find("Label").text
            xtal.Login = x.find("Login").text
            xtal.Sample = x.find("Sample").text
            xtal.idSample = int(x.find("idSample").text)
            xtal.Column = int(x.find("Column").text)
            xtal.Row = x.find("Row").text
            xtal.Shelf = int(x.find("Shelf").text)
            xtal.Comments = x.find("Comments").text
            xtal.offsetX = float(x.find("offsetX").text) / 100.0
            xtal.offsetY = float(x.find("offsetY").text) / 100.0
            xtal.IMG_URL = x.find("IMG_URL").text
            xtal.IMG_Date = x.find("IMG_Date").text
            xtal.ImageRotation = float(x.find("ImageRotation").text)
            xtal.SUMMARY_URL = x.find("SUMMARY_URL").text
            pp.Plate.Xtal.append(xtal)
        return pp
    except:
        return
>>>>>>> origin/master
