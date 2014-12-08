#!/usr/bin/python2.7

"""
	No real explanation, just gather all links from hzz page and fill rtf file with details
"""

import threading
import time
import urllib
import os
import lib.ItemObject
import xml.etree.ElementTree as ElementTree
from datetime import date, timedelta, datetime


sendMail = True 
#store all relevant files in app root folder
scriptpath = '/home/user/Documents/hzzapp/'
urls = ["http://burzarada.hzz.hr/rss/rsskat1002.xml", "http://burzarada.hzz.hr/rss/rsskat1003.xml", "http://burzarada.hzz.hr/rss/rsskat1014.xml", "http://burzarada.hzz.hr/rss/rsskat1018.xml", "http://burzarada.hzz.hr/rss/rsskat1011.xml"]
msgTxtFile = scriptpath + "msgtext.txt"
rssfile = scriptpath + "hzzrss.xml"
sentLogiFile = scriptpath + "sent.log"
passedLogFile = scriptpath +  "passed.log"


#open log file
logfp = open(scriptpath + 'log', 'a+')
#rewind file pointer
logfp.seek(0)


#extract last run time
line = ""
for line in logfp:
	pass

#extract last run time
# base search for new items based on timespan; if first run give timespan of 5 days otherwise calculate timespan
if line == "":
	lastrun = timedelta(days=5)
else:
	try:
		lastrun = (datetime.today() - datetime.strptime(line.split('\t')[0], "%d/%m/%Y"))
	except:
		print "could not parse log file, exiting"
		exit(1)



#open sent and nonsent logs
sentLog = None
passedLog = None


#exit only if sentlog has error
try:
	sentLog = open(sentLogiFile, 'a+')
	passedLog = open(passedLogFile, 'a+')
except:
	if sentLog == None:
		print "could not open sent log, exiting"
		exit()
	else:
		print "passed log opening problem"


resultStrs = list()

for url in urls:

	rss = None

	try:
		#fuck it needs to be saved into tmp document
		try:
			urllib.urlretrieve(url, rssfile)
		except:
			resultStrs.append('cannot retrive rss feed')
	
		if os.path.isfile(rssfile):
			rss = ElementTree.parse(rssfile).getroot()	
		
			os.unlink(rssfile)
		else:
			resultStrs.append('cannot open rss tmp file')
	
	except Exception as ex:
		resultStrs.append('could not parse input source')

	if rss != None:
		print 'processing url: '+url
		items = list()



		#DEVELOPMENT SINGLE CALL
		#test = lib.ItemObject.ItemObject('http://burzarada.hzz.hr/RadnoMjesto_Ispis.aspx?WebSifra=66967193', 'testtitl')
		#test.start()
		#test.join()
		#exit()


		#itterate througt item nodes, parsing only nodes that have publish date equal or greather than last run date
		#FIXME: check reason why this method will send messages only once		
		for item in rss.iter('item'):
			try:
				itemDate = datetime.strptime(item.find('pubDate').text, "%d.%m.%Y")
				#check if item was published after last run, round up on day!!!
				#comaprison doesnt take into considiration future time in log file, for this scenarion beaviur is underterment
				if (datetime.today() - itemDate).days <= lastrun.days:
					items.append([item.find('link').text, item.find('subject').text])
			except Exception as ex:
				print ex
				pass

		if len(items) > 0:
			threads = [None for x in range(0,len(items))]
			for i in range(0, len(items)):
				threads[i] = lib.ItemObject.ItemObject(items[i][0], items[i][1], scriptpath, sendMail)
				threads[i].start()
			
			for x in threads:
				x.join()
				while x.is_alive():
					time.sleep(0.1)

			succapplys = 0
			#FIXME: record the results
			for x in threads:
				sent, guid, title, url1, addresses = x.Results()
				if sent:
					sentLog.write("{0};{1};{2};{3};{4}\n".format(guid,date.today().strftime("%d/%m/%Y"),title.encode('utf-8'), url1, addresses)) 
					succapplys += 1
				else:
					if passedLog != None:
						passedLog.write("{0};{1};{2};{3};{4}\n".format(guid, date.today().strftime("%d/%m/%Y"), title.encode('utf-8'), url1, addresses))

			if succapplys > 0:
				resultStrs.append("For source:{0} there were {1} job offers and email was sent to {2}".format(url, len(threads), succapplys))
			else:
				resultStrs.append("For source: {0} there were {1} job offers for none of msg was sent".format(url, len(threads)))
		
		else:
			resultStrs.append('For source {0} there are no items to apply on'.format(url))	

	#break other sources if in development mode
	if not sendMail:
		break

if len(resultStrs) == 0:
	resultStrs.append('Default run message');

logfp.write("{0}\t{1}\n".format(date.today().strftime("%d/%m/%Y"), ';'.join(resultStrs)))

logfp.close()
