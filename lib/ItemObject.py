#_*_ coding: utf-8 _*_
""" Class for applaying to each item from rss feed,
	Implemented for multithreading fasion
"""

import uuid
import urllib
import threading
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import path
from lib.DetailsPageParser import DetailsPageParser

class ItemObjectException(Exception):
	def __init__(self, msg, instanceSpecific=False):
		self.value = msg
		self.breakOthers = not instanceSpecific
	def __str__(self):
		return repr(self.value)


class ItemObject(threading.Thread):
	
	#static shared function for item categorization
	CategorizeItem = None
	
#FIXME: create variables that are needed for multithreading and see what return values will be needed
	
	def __init__(self, hzzid, url, title, configObj, workpath):
		threading.Thread.__init__(self)
		self.Sent = False
		self.subject = title
		self.hzzid = hzzid
		self.cfg = configObj
		self.workpath = workpath
		self.errorMsg = None #FIXME: dont forget about exceptions
		self.PropObj = None
		self.itemClass = 'general'
				
		#user data and required configuration values
		try:
			self.UNAME, self.MYEMAIL = self.cfg.Read('user', username=None, emailaddress=None).values()
			self.smptServer = self.cfg.Read('smtp', server=None)
			#read mail configuuration if provided
			self.smtpCfg = self.cfg.Read('smtp', SSL=False, uname="", pwd="")
		except:
			raise ItemObjectException('User section of config file contains error')
			
		#optional configuratioin values
		#FIXME: read optional configuration files and create html parser obj?
		
		#class specific values
		self.targetEmailList = []
		self.url = url
		self.TITLE = title
		self.id = uuid.uuid1()
		self.msgVariablePattern = re.compile(r"({\w+})")
		
		
		#for dynamic cv addresses sutomatically append guid value as id value
		#CVURL is anyway dependent on occurance in the message
		try:
			self.CVURL = self.cfg.Read('user', cvurl=None)
			if self.CVURL != None and self.CVURL[-4:] == '.php':
				self.CVURL += '?%s' % urllib.urlencode({'id':self.id})
		except:
			pass
		
	def Results(self):
		""" Return, something, referr to notes
		"""
		if self.PropObj == None:
			print 'see what to do in the case prop obj is none'
			return " "
		else:
			return [str(self.id), self.hzzid, self.subject, self.itemClass, self.PropObj.employee, \
				";".join(self.PropObj.emails), self.PropObj.contactStr]
# 			return [str(self.id), self.hzzid, unicodedata.normalize('NFKD', unicode(self.subject, 'utf-8')).encode('ascii', 'ignore'), \
# 				self.itemClass, unicodedata.normalize('NFKD', unicode(self.PropObj.employee, 'utf-8')).encode('ascii', 'ignore'), \
# 				";".join(self.PropObj.emails), \
# 				unicodedata.normalize('NFKD', unicode(self.PropObj.contactStr, 'utf-8')).encode('ascii', 'ignore')]
			#FIXME: remains object properties, but first deal with item classes
	
	def run(self):
		#create parser obj
		#FIXME: configure paser obbject
		parseObj = DetailsPageParser()
		
		parsed = False
		
		#try to retrive details page, fixme: move to function there is a problem with socket connection
		try:
			res = urllib.urlopen(self.url)
			parseObj.feed(res.read())
			parsed = True
		except Exception as ex:
			self.errorMsg = 'Parsing error: ' + ex.__str__()
# 			if self.cfg.Read('DEBUG'):
# 				print dir(ex)
		
		#extract message properties and determine object type
		self.PropObj = parseObj.prop
		
		
		#proceede with sending if parsing went fine
		if self.errorMsg == None:
			if self.categorize():
				#make additional check whater msg is hzz osposobljavanje
				if self.cfg.Read('hzz', osposoljavanje=True) or not self.PropObj.osposobljavanje:
					self.sendMessage()


	def categorize(self):
		""" Categorize obbject into one of the following categories:
			general -> sends general msg, this is default value
			targeted -> if math for targeted position was found, sends targeted msg
			filtered -> item type doesn't fullfill requirements for sending a msg
			hzzspectial -> spectial message for assholes in hzz
			return value boolean indicating if the message should be sent
		"""
		send = len(self.PropObj.emails) > 0
		#first check if msg is targeted or filtered
		catg = 0
		if ItemObject.CategorizeItem != None:
			catg = ItemObject.CategorizeItem(self)
		
		#not a best approach but just process type class as strings
		#fixme: see if installation of enum class is worth it
		if catg == 1:
			self.itemClass = 'targeted'
		elif catg == -1:
			self.itemClass = 'filtered'
			send = False
		
		#for me hzz spectial is somehow important so check for this category comes last
		#also this cannot be targeted/filtered item because this is i...
		#determine this by @hzz substring in emails list
		#override even filtered category
		for email in self.PropObj.emails:
			if email.find('@hzz.hr') > 0:
				#check if this feature is enabled
				if self.cfg.Read('hzzspecial', enable=True):
					#fixme, maybe add address burrzarada@hzz.hr
					send = True #override sending argument
					self.itemClass = 'hzzspectial'
					break
		
		return send

	def sendMessage(self):
		#prepapre messagae
		msg = None
		
		#testing other types of classes
# 		self.itemClass = 'hzzspectial'
		
		try:
			section = 'generalmail' #change section according to itemClass (default general)
			if self.itemClass == 'hzzspectial':
				section = 'hzzspecial'
			elif self.itemClass == 'targeted':
				section = 'hitmail'
			
			msg = self.readMailTemplate(self.cfg.Read(section, msgtemplate=None))
	
			#populate the message
			msg['Subject'] = self.cfg.Read(section, msgsubject="Javljanje na natječaj") + " " + self.TITLE 
			#sender
			msg['From'] = self.MYEMAIL
			#targets
			#FIXME give additional check for development?
			self.PropObj.emails = ['hrvoje@zlatnodoba.hr']
 			msg['To'] = ', '.join(self.PropObj.emails)
			
			#add attahments if any
			
			
		except:
			self.errorMsg = 'cannot create message'
			
		#test for the msg and common msg fields
		if msg != None:
			if self.cfg.Read('SENDMAIL'):
				if self.smtpCfg['SSL']:
					server = smtplib.SMTP_SSL(host=self.smptServer, port=465) #FIXME: introduce variable for the port
					server.ehlo() #for test server init connection is needed
				else:
					server = smtplib.SMTP(self.smptServer)
					server.helo() #call connection for possible login purpposes, havent read documentation
					
				#login if needed
				if self.smtpCfg['uname'] != "":
					server.login(self.smtpCfg['uname'], self.smtpCfg['pwd'])
				#send the message
				try:
					server.sendmail(msg['From'], msg['To'], msg.as_string())
					self.Sent = True
				except Exception as ex:
					self.errorMsg = 'Mail server error: ' + ex.__str__()
					
			else:
				if self.cfg.Read('DEBUG'):
					pass				
					self.Sent = True #for debbugging purposes

		else:
			#store information on message error
			self.errorMsg = 'Cannot create e-mail message'
			
		

	def readMailTemplate(self, templname):
		""" reads template and returns multipart objec containing text and html parts
		"""
		try:
			fp = open(path.join(self.workpath, templname), 'r')
		except Exception as ex:
# 			print ex
			return None
		
		msgTXT = ""
		msgHTML = ""
		
		for line in fp:
			msgTXT += self.putContent(line, False)
			msgHTML += self.putContent(line, True)
		
		fp.close()
		
		if msgTXT != "" and msgHTML != "":
			msg = MIMEMultipart('alternative')
			
			parttxt = MIMEText(msgTXT.encode('utf-8'), 'plain')
			parttxt.set_charset('utf-8')
			msg.attach(parttxt)

			try:
				parthtml = MIMEText(msgHTML.encode('utf-8'), 'html')
				parthtml.set_charset('utf-8')
				msg.attach(parthtml)
			except Exception as ex:
				pass #html part is optional
			
			return msg
		
		return None #default behaviour
	

	def putContent(self, txt, htmlWrap):
		""" Replace variables in msg text with real values
		"""
		offset=0 #offset for multiple string replacmets
		for m in self.msgVariablePattern.finditer(txt):
			try:
				#special case url for html
				repStr = getattr(self, m.group()[1:-1]).encode('UTF-8')
				if m.group() in ['{CVURL}', '{url}'] and htmlWrap:
					txt = txt[:m.start()+offset] + '<a href="{0}">ovom linku</a>'.format(repStr) + txt[m.end()+offset:]
				else:
					txt = txt[:m.start()+offset] + repStr +  txt[m.end()+offset:]
					
				offset += len(repStr) - len(m.group())
				
			except Exception as e:
				#just in case replace variable
				txt = txt[:m.start()] + txt[m.end():]


		if htmlWrap:
			if txt !=  "\n":
				return '<p>{0}</p>\n'.format(txt)
			else:
				return ""
		else:
			return txt.replace('<br>', '\n')

		