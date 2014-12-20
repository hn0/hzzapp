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
	
#FIXME: create variables that are needed for multithreading and see what return values will be needed
	
	def __init__(self, url, title, configObj, workpath):
		threading.Thread.__init__(self)
		self.Sent = False
		self.cfg = configObj
		self.workpath = workpath
		self.errorMsg = None #FIXME: dont forget about exceptions
		self.PropObj = None
				
		#user data and required configuration values
		try:
			self.UNAME, self.MYEMAIL, self.msgtemplate = self.cfg.Read('user', username=None, emailaddress=None, msgtemplate=None).values()
			self.msgtemplate = path.join(self.workpath, self.msgtemplate)
			self.smptServer = self.cfg.Read('smtp', server=None)
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
		
	
	
	def run(self):
		#create parser obj
		#FIXME: configure paser obbject
		parseObj = DetailsPageParser()
		
		test = "none"
		
		#try to retrive details page, fixme: move to function there is a problem with socket connection
		try:
			res = urllib.urlopen(self.url)
			parseObj.feed(res.read())
		except Exception as ex:
			self.errorMsg = 'Cannot retrieve details page'
			test = ex
		
		#extract message properties and determine object type
		self.PropObj = parseObj.prop
		
		
		print 'determine Item type based on prop object'
		
		#check if email will be sent IN PARSER OBJECT CONSTURCT EMAIL ADDRESS FOR HZZ!
		#FIME: etract information from parsed object
		#self.sendMessage()		


	def sendMessage(self):
		
		#FIXME: pass type of the message
		#print len(self.targetEmailList)
		
		#here should go code that decides which type of msg will be created
		
		msg = None
		
		msg = self.readMailTemplate(self.msgtemplate)
		
		#test for the msg and set fields like Subject, to, from
		if msg != None:
			print(msg)
		else:
			print('SHIT')
		
		
		return False
		if not self.sendMail:
		#print "message sending disabled"
			return True

		#once again debug test, on my mail address
		#self.targetMailList = ['hrvoje@zlatnodoba.hr']

		if len(self.targetMailList) > 0:
			
					#TODO: add this information as well
			
			msg = MIMEMultipart('alternative')
		 	msg['Subject'] = 'Javljanje na natjecaj ' + self.TITLE
			msg['From'] = 'Hrvoje Novosel<hnovosel@live.com>'	
			msg['To'] = ', '.join(self.targetMailList)


	
			#create smtp obj, use zlatnodoba for now!
			server = smtplib.SMTP_SSL(host='smtp.zlatnodoba.hr', port=465)
			server.ehlo()
			server.login('hrvoje@zlatnodoba.hr', 'ZnVuk00ES')
			try:
				server.sendmail('Hrvoje Novosel<hnovosel@live.com', self.targetMailList, msg.as_string())
				#assume that msg was sent sucessfully
				return True
			except:
				pass
			#also by default return false
			return False
		else:
			return False

	def readMailTemplate(self, templname):
		""" reads template and returns multipart objec containing text and html parts
		"""
		try:
			fp = open(templname, 'r')
		except:
			return None
		
		msgTXT = ""
		msgHTML = ""
		
		for line in fp:
			msgTXT += self.putContent(line, False)
			msgHTML += self.putContent(line, True)
		
		fp.close()
		
		if msgTXT != "" and msgHTML != "":
			msg = MIMEMultipart('alternative')
			
			parttxt = MIMEText(msgTXT, 'plain')
			msg.attach(parttxt)
			
			parthtml = MIMEText(msgHTML, 'html')
			msg.attach(parthtml)
			
			return msg
		
		return None #default behaviour
	

	def putContent(self, txt, htmlWrap):
		""" Replace variables in msg text with real values
		"""
		for m in self.msgVariablePattern.finditer(txt):
			try:
				#special case url for html
				if m.group() == '{CVURL}' and htmlWrap:
					txt = txt[:m.start()] + '<a href="{0}">ovom linku</a>'.format(getattr(self, m.group()[1:-1])).encode('UTF-8') + txt[m.end():]
				else:
					txt = txt[:m.start()] + getattr(self, m.group()[1:-1]).encode('UTF-8') +  txt[m.end():]
			except Exception as e:
				#just in case replace variable
				txt = txt[:m.start()] + txt[m.end():]


		if htmlWrap:
			return '<p>{0}</p>\n'.format(txt)
		else:
			return txt.replace('<br>', '\n')

