#_*_ coding: utf-8 _*_
"""
    FIXME: WRITE SOME DESCRRIOPTIOJN

    Author: Hrvoje Novosle<hnovosel@live.com>
    Created:?

"""
from HTMLParser import HTMLParser
import re
import unicodedata

class SearchObject:
    """ Abstract class for search objects
    """
    def __init__(self, resTarget):
        self.resTarget = resTarget

    def Inspect(self, data):
        """ Astract method for inspection of passed data, returns boolean indicating result found method
        """
        raise NotImplemented()
    
    def BreakTag(self):
        return None
    
class OsposoljavanjeSearch(SearchObject):
    
    def Inspect(self, data):
        
        if 'osposobljavanje' in  data.lower():
            self.resTarget.osposobljavanje = True
        return True #this is element value object

class PoslodavacSearch(SearchObject):
    
    def Inspect(self, data):
        self.resTarget.Add(data, 'employee')
        return True #also element text search

class KontaktSearch(SearchObject):
    
    def __init__(self, resTarget):
        self.resTarget = resTarget
        self.phonePattern = re.compile(':\s?[0-9]')
    
    def Inspect(self, data):
        #ok, some of the strings shuld be filtered
        if data.strip().lower() not in ['kontakt:', 'e-mailom:']:
            #next email addresses should be filtered as well #and phones
            if data.find('@') == -1 and not self.phonePattern.search(data):
                self.resTarget.Add(data, 'contact')
        return False

    def BreakTag(self):
        return 'hr' #it does seem that every section is bbroken with hr tag


class HzzSpectialSearch(SearchObject):
    
    def __init__(self, resTarget):
        self.resTarget = resTarget
        self.namePattern = re.compile('([a-zA-Z]+)\s([a-zA-Z]+)')
    
    def Inspect(self, data):        
        matchstr = unicodedata.normalize('NFKD', unicode(data, 'utf-8')).encode('ascii', 'ignore')
        res = self.namePattern.search(matchstr)
        if res: #fixme, cconver to search!!!
            self.resTarget.Add("{0}.{1}@hzz.hr".format(res.group(1).lower(), res.group(2).lower()), 'email')
            self.resTarget.Add("{0}.{1}@hzz.hr".format(res.group(2).lower(), res.group(1).lower()), 'email')
            
    
    def BreakTag(self):
        return 'span' #this field is contained uunder span element for now


#Enumerations for oglas types
class ItemProperties():
#     types = ['email', 'postoffice']
#     destination = []
    
    def __init__(self):
        self.emails = []
        self.postoffices = []
        self.employee = "-"
        self.contactStr = ""
        self.osposobljavanje = False
    
    def Add(self, value, type=""):
        """ Add item delivery options
        """
        if type == 'email':
            self.addemail(value)
        elif type == 'employee':
            self.employee = value
        elif type == 'contact':
            self.contactStr += value #see if any additional operations are necessary here
        
    
    def addemail(self, address):
        if address not in self.emails:
            self.emails.append(address)
    #FIXME: add destination method

class DetailsPageParser(HTMLParser):

    def __init__(self):
        """ Write down class dscription
        """
        HTMLParser.__init__(self)
        self.prop = ItemProperties()

        #for pattern refer to: http://nbviewer.ipython.org/github/rasbt/python_reference/blob/master/tutorials/useful_regex.ipynb
        self.emailPattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        
        #search list
        self.idMarkerTags = {'lblVrstaZaposlenja': OsposoljavanjeSearch(self.prop), 'lblNazivPoslodavca' : PoslodavacSearch(self.prop), \
                             'lblKontaktKandidataText': KontaktSearch(self.prop), 'lblSavjetodavac': HzzSpectialSearch(self.prop)} 
        
        self.searchMarker = None

    
    def handle_starttag(self, tag, attrs):
        """ Set search string if tag + attriburte matces, searches for e-mail address in tags
        """
        #first deal with potential email addresses in href tag, once again always have this search active
        if tag == 'a':
            addr = [x[1][7:] for x in attrs if x[0] == 'href'] #remove mailto part
            if self.emailPattern.match(addr[0]):
                self.prop.Add(addr[0], 'email')
        
        #implement search marker method, based on attr marker
        if len(attrs) > 0:
            idval = [x[1] for x in attrs if x[0] == 'id']
            if len(idval) > 0:
                if idval[0] in self.idMarkerTags.keys():
                    self.searchMarker = self.idMarkerTags[idval[0]]
        


    def handle_endtag(self, tag):
        if self.searchMarker != None and self.searchMarker.BreakTag() == tag:
            self.searchMarker = None

    def handle_data(self, data):
        """ React only to search string rendering page invalid if match is found
        """
        if len(data.strip()) > 0:
        
            #regardless to all search for e-mail address
            address = self.emailPattern.search(data)
            if address:
                self.prop.Add(address.group(0), 'email')
            
            
            #go througth search markers
            if self.searchMarker != None:
                if self.searchMarker.Inspect(data):
                    self.searchMarker = None #reset search marker

        
