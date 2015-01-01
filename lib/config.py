#_**_ coding: utf-8 _*_
"""

Module for parsing configuration files

Application will use hard coded configuration file for its behaviur

hzzapp.conf in root directory should be written according to RFC 8822 style

Created 10. Dec 2014
Author: Hrvoje Novosel<hnovosel@live.com>
"""


import ConfigParser


#classes for exceptions
class SectionNotFound(Exception):
    def __init__(self, sectionName):
        self.value = "Section "+sectionName+" cannot be found in configuration file"
    def __str__(self):
        return repr(self.value)
#exception risen when specific keyword for given configuration value was not found
class KeyNotFound(Exception):
    def __init__(self, sectionName, keyName):
        self.value = "Key "+ keyName +" (under section "+ sectionName +") cannot be found in configuration file"
    def __str__(self):
        return repr(self.value)
#exception risen when missmatch between requested type and type of configuration value occur, not implemented yet
class KeyIncorrectType(Exception):
    def __init__(self, key, expectedType, realType):
        self.value = "Key "+ key + " has type "+ realType +" but "+ expectedType +" was expected"
    def __str__(self):
        return repr(self.value)



class config:
    def __init__(self, configfile):
        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.read(configfile)
        
    def Read(self, section, **keys):
        #special case debug, for simplicity define here, maybe it should go to configuration file
        if section.upper() in ['DEBUG', 'DEVELOPMENT']:
            return False
        elif section.upper() == 'SENDMAIL':
            return False
        
        #wrap retrive methods, return default value if passed, otherwise raise exception
        try:
            if len(keys) == 1:
                item = keys.popitem()
                return self.getValue(section, item[0], type(item[1]))
            else:
                for k in keys:
                    keys[k] = self.getValue(section, k, type(keys[k]))
                return keys
        except (KeyNotFound):
            if len(keys) == 0 and item[1] != None:
                return item[1]
            elif len(keys) > 0 and True not in [keys[x] == None for x in keys]:
                return keys
            #by default rerise exception
            raise
        
    def getValue(self, section, name, type=type(" ")):
        if not self.cfg.has_section(section):
            raise SectionNotFound(section)
        
        if not self.cfg.has_option(section, name):
            raise KeyNotFound(section, name)
        
        
        #return typed response
        if type is bool:
            return self.cfg.getboolean(section, name)
        elif type is int:
            return self.cfg.getint(section, name)
        elif type is float:
            return self.cfg.getfloat(section, name)
        else:
            return self.cfg.get(section, name)
        
        
        
        