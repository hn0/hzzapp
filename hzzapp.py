#!/usr/bin/python2.7
#_*_ coding: utf-8 _*_

"""



This script is a free software and you can redistribute and/or modify it under terms of GNU General Public
License as published by the Free Software Fundation (http://www.gnu.org/copyleft/gpl.html)

Disclaimer
This script is written and distributed with good intentions and in desire that someone will find it useful. 
However it's distributed "AS IS" and without any warranty of any kind. 
For any possible usage of this software you acknowledge and agree that original author of this script 
makes no representation to the adequacy of this script for your needs, or that script will be error free.
Under no event, arising in any way from usage of this software, author shall be liable for any direct, 
indirect, consequential or any other kind of damage (including, but not limited to loss of data or profits; 
or business interruption) however caused and on any theory of liability.

Creation date: 9. Dec 2014
Author: Hrvoje Novosel<hnovosel@live.com>
"""

import sys
import threading
import urllib
import tempfile
import re
import time
import xml.etree.ElementTree as ElementTree
from os import path
from datetime import timedelta, datetime
from lib.ItemObject import ItemObject, ItemObjectException
from lib.config import config
from lib.ItemFilter import ItemFilter

#maybe there is better way but insuure that utf-8 is selected codec
reload(sys)
sys.setdefaultencoding('utf-8')

#global variables
workpath = path.dirname(__file__) #always use path..join so paths relative to the scripts folder can be used as well
dateFormat = "%d/%m/%Y %H:%M:%S"

logmsgs = []

def writeLogEntery(logfp, msg):
    logfp.write("{0}\t{1}\n".format(datetime.now().strftime(dateFormat), msg))

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
            seekTimeSpan = datetime.now() - datetime.strptime(line.split('\t')[0], dateFormat)
            #FOR DEVELOPMENT ONLY
#             seekTimeSpan = timedelta(days=30)
#             print 'time delta manually set'
        
        #open sent log (create files and append variable names if files are not present)
        logheaderstr = "\t".join(['ItemID', 'HzzID', 'Subject', 'ItemClass', 'Employee', 'emali', 'contactinfo'])
        presentSent = path.isfile(path.join(workpath, cfg.Read('app',sentlog=None)))
        presentPassed = path.isfile(path.join(workpath, cfg.Read('app',passedlog=None)))
        #Maybe sent log should not fall into category of errors with log file but this is point that can be addressed later
        sentfp = open(path.join(workpath, cfg.Read('app',sentlog=None)), 'a+')        
        passedfp = open(path.join(workpath, cfg.Read('app', passedlog=None)), 'a+')
        
        skipidvalues = []
        
        if not presentSent:
            writeLogEntery(sentfp, logheaderstr)
        else:
            sentfp.seek(len(logheaderstr) + 21) #add 20 for date
            for line in sentfp:
                parts = line.split('\t')
                try:
                    if seekTimeSpan + seekTimeSpan + timedelta(days=2) > datetime.now() - datetime.strptime(parts[0], dateFormat):
                        skipidvalues.append(parts[2])
                except:
                    pass #dont rise huss if date parsing fails
                
        if not presentPassed:
            writeLogEntery(passedfp, logheaderstr)
        else:
            passedfp.seek(len(logheaderstr) + 21) #add 20 for date
            for line in passedfp:
                parts = line.split('\t')
                try:
                    if seekTimeSpan + timedelta(days=2) > datetime.now() - datetime.strptime(parts[0], dateFormat):
                        skipidvalues.append(parts[2])
                except:
                    pass #dont rise huss if date parsing fails
                #FIXME: PROBLEM WITH PARSING AND MODEL OF ITEM DATETIME CHECKING
        
        #last prepare filter object, and pass it as static variabble
        filterObj = ItemFilter(cfg, workpath)
        ItemObject.CategorizeItem = filterObj.CategorizeItem 
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
                    #here extraction of id is needed
                    link = item.find('link').text
                    id = None
                    for x in idreg.findall(link):
                        id = x #keep last id
                    #time test condition
                    if id:
                        #next is test for already sent items, test is disabled in debbug mode
                        #different conditions for first run and consiquential runs
#                         print len(skipidvalues)
                        if (len(skipidvalues) > 0 and id not in skipidvalues) or (len(skipidvalues) == 0 and (currentTime - datetime.strptime(item.find('pubDate').text, "%d.%m.%Y")).days <= seekTimeSpan.days):
                            items.append([id, link, item.find('subject').text])
                            if cfg.Read('DEBUG'):
                                break;
                                            
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
                        threads[i] = ItemObject(items[i][0], items[i][1], items[i][2], cfg, workpath)
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
                            
                            #check for possible errors, if any occures ignore current item
                            #in the next run of the script same item will be once again parsed (giving possiility of socket connection refused error not occuring duuring following runs)
                            if t.errorMsg == None:
                                #create res list and use it to writte to desirred output file
                                resStr =  "\t".join(t.Results())
                                resDest = sentfp if t.Sent else passedfp
                                
                                writeLogEntery(resDest, resStr)
                                
                            #else:
                                #leave possibility of item level error loging
                            
            
            if noErrors: #dont append source result msg
                appout.append("In source: {0} there were: {1} items; {2} new items found; {3} application sent".format(src, totalItem, len(items), len([x for x in threads if x != None and x.Sent == True]) ))
            else:
                appout.append("Error occured during processing items from source: {0}".format(src))
                break #there is no point in parsing other sources if this one is fail? 
    
    #on exit of application write down log file, by default use log file
    outmethod = cfg.Read('app', output='log')
    
   #rewrite those statments
    if len(outmethod.split('|')) == 1:
        p = logfp if outmethod == 'log' else sys.stdout
        for x in appout:
            writeLogEntery(p, x)
    else:
        for x in appout:
            writeLogEntery(sys.stdout, x)
            writeLogEntery(logfp, x)
    
    #close all open files
    logfp.close()
    sentfp.close()
    passedfp.close()
    
#start the application
if __name__ == '__main__':
    hzzapp_main()
