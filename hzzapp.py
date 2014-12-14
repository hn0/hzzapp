#!/usr/bin/python2.7
#_*_ coding: utf-8 _*_

"""
Hzz application, parser rss feeds from hzz web pages and automatically applys to posted job possitions


This script is distributed with good intentions and desire that someone will find it useful. However its distributed
without any warranty and
AUTHOR will not take any responsibbility for its usage!!! IMPROVE THIS 
This script is distributed in desire that one will find it useful but without any warranty and taking 
any responsibility from authors side for p
possible misuse of this script.

FINISH WRITING DISCLAMER


This script is a free software and you can redistribute and/or modify it under terms of GNU General Public
License as published by the Free Software Fundation (http://www.gnu.org/copyleft/gpl.html)

Creation date: 9. Dec 2014
Author: Hrvoje Novosel<hnovosel@live.com>
"""

import sys
import threading
import urllib
import tempfile
import re
import xml.etree.ElementTree as ElementTree
from os import path
from datetime import time, timedelta, datetime
from lib.ItemObject import ItemObject, ItemObjectException
from lib.config import config

#global variables
workpath = path.dirname(__file__) #always use path..join so paths relative to the scripts folder can be used as well

logmsgs = []

def writeLogEntery(logfp, msg):
    logfp.write("{0}\t{1}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), msg))

def hzzapp_main():
    #first load application configuration
    try:
        cfg = config(path.join(workpath, 'hzzapp.conf'))
    except:
        #no preferences for out, use std err
        print >> sys.stderr, 'Could not open configuration file, exiting'
        exit(1)
    
    #open log file, one entery to the log must be entered regardless to output settings
    #sent log is also essential for application operating 
    #additionally retrive last launched date as well as list of applied vaccineis
    try:
        #if logfile doesnt exist, create one
        logfp = open(path.join(workpath,cfg.Read('app', logfilename='log')), 'a+')
        logfp.seek(0)
        
        #get last runtime
        line=""
        for line in logfp:
            pass
        
        if line == "":
            seekTimeSpan = timedelta(days=cfg.Read('app', inittimespan=1))
        else:
            seekTimeSpan = datetime.now() - datetime.strptime(line.split('\t')[0], "%d/%m/%Y %H:%M:%S")
            #FOR DEVELOPMENT ONLY
            seekTimeSpan = timedelta(days=5)
            print 'time delta manually set'
        
        #open sent log
        #FIXME: parse enteries from sent log?
        #Maybe sent log should not fall into category of errors with log file but this is point that can be addressed later
        sentfp = open(path.join(workpath, cfg.Read('app',sentlog=None)), 'a+')
        
    except:
        print >> sys.stderr, 'Could not open necessary log files, exiting'
        exit(1)
    
    #regardles to output setting write current runtime into log file
    writeLogEntery(logfp, 'Application was launched')
    
    sources = ""
    appout = []
    
    #go througth sources
    try:
        sources = cfg.Read('hzz', urllist=None)
    except:
        appout.append("Sources are not configured properly")
    
    for src in sources.split(','):
        #do the main lift here, first construct tmp file
        rss = None
        with tempfile.NamedTemporaryFile(mode='w+') as tmp:
            try:
                urllib.urlretrieve(src, tmp.name)
            except Exception as ex:
                appout.append("Cannot retive source: " + src)
                continue
            #parse tmp file
            try:
                rss= ElementTree.parse(tmp).getroot()
            except:
                appout.append("Cannot parse xml for source: " + src)
                continue
        
        #continue with init of found apply objects
        if rss != None:
            idreg = re.compile(r'\d+$') #regex expresion for id extraction
            items = []
            currentTime = datetime.now()
            
            totalItem = 0
            for item in rss.iter('item'):
                try:
                    #time test condition
                    #IDIOTS ONLY PROVIDE DATE
                    if (currentTime - datetime.strptime(item.find('pubDate').text, "%d.%m.%Y")).days <= seekTimeSpan.days: #round comparison on the same day
                        #here extraction of id is needed
                        link = item.find('link').text
                        id = None
                        for x in idreg.findall(link):
                            id = x #keep last id
                        
                        #FIXME: NEXT TEST FOR ID ENTERTY IN SENT LOG!!!
                        
                        if id and True:
                            items.append([id, link, item.find('subject').text])
                                            
                except Exception as ex:
                    if cfg.Read('DEBUG'):
                        print ex
                    pass #really keep it quiet if item adding fails
                finally:
                    totalItem += 1
            
            threads = [None for x in range(0, len(items))]
            noErrors = True #flag for complete item object process
            #start items
            if len(items) > 0:
                for i in range(0, len(items)):
                    #use long jump that will break loop if objet initialization error occures (invalid configuration)
                    try:
                        threads[i] = ItemObject(items[i][1], items[i][2], cfg, workpath)
                        threads[i].start()
                    except ItemObjectException as ex:
                        appout.append(ex)
                        if ex.breakOthers:
                            noErrors = False
                            break #here execution of rest of the items is irelevant, they will all have same error
                        
                #join back threads
                if noErrors:
                    for t in threads:
                        if t != None:
                            while t.is_alive():
                                time.sleep(0.01)
                            t.join()
                            #FIXME: inspect results and write sent log, but first deal with run command
            
            if noErrors: #dont append source result msg
                appout.append("In source: {0} there were: {1} items; {2} new items found; {3} application sent".format(src, totalItem, len(items), len([x for x in threads if x != None and x.Sent == True]) ))
            else:
                appout.append("Error occured during processing items from source: {0}".format(src))
                break #there is no point in parsing other sources if this one is fail? 
    
    #on exit of application write down log file, by default use log file
    outmethod = cfg.Read('app', output='log')
    
    if len(outmethod.split('|')) == 1:
        p = logfp if outmethod == 'log' else sys.stdout
        for x in appout:
            writeLogEntery(p, x)
    else:
        for x in appout:
            writeLogEntery(sys.stdout, x)
            writeLogEntery(logfp, x)
    
#start the application
if __name__ == '__main__':
    hzzapp_main()
