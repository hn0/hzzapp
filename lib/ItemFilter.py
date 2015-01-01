#_*_ coding: utf-8 _*_

"""
TODO: write something


Created: 25. Dec 2014

"""


import difflib
from os import path

class ItemFilter:
    """ For first release this functionality is not primary concern
        This is area that could be intresting for extension, even with learning algoritham but for now not really relevant for functioning of the application
        Simple implementation will be implementation that will filter out based on root of wordlist
    """
    
    def __init__(self, cfg, workpath):
        """ Read just simple file list, enteries in new line
            Wordlist in lower or upper case?
        """
        self.filterWords = []
        
        #just try to open filter words list, fail without notificatins
        try:
            file = path.join(workpath, cfg.Read('app', filterlist=None))
            with open(file, 'r') as fp:
                for line in fp:
                    if len(line) > 1:
                        self.filterWords.append(line.rstrip())
        except Exception as ex:
            if cfg.Read('DEBUG'):
                print ex
            pass
        
        
    def CategorizeItem(self, ItemObj):
        """ 
            Retruns item category flag:
            -1 Item should be filtered and no email should be sent
             0 There is nothing to say about items category
             1 Item falls into targeted applications
        """
        
        
        #FIXME: comparison of the strings should use some kind of distance function, eg Levenshtain??
        #perform search if filterwords list isnt empty
        if len(self.filterWords) > 0:
            for w in ItemObj.subject.split(' '):
                if len(w) > 3 and len(difflib.get_close_matches(w.lower(), self.filterWords, cutoff=.7)) > 0: #maybe intresting function?
                    #return this class as filtered one
                    return -1
        
        return 0 #default value