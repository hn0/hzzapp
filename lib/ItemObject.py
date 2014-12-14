#_*_ coding: utf-8 _*_
""" Class for applaying to each item from rss feed,
	Implemented for multithreading fasion
"""

import uuid
import urllib
import threading
import re
import smtplib
from HTMLParser import HTMLParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class ItemObjectException(Exception):
	def __init__(self, msg, instanceSpecific=False):
		self.value = msg
		self.breakOthers = not instanceSpecific
	def __str__(self):
		return repr(self.value)


class DetailsPageParser(HTMLParser):

	def __init__(self):
		""" Define target tags and elements that needs to be parsed
		"""
		self.valid = True #by default assume that this is valid vaccenies (this variable should take into consideration number of found email addresses)
		HTMLParser.__init__(self)
		self.targetMails = []
		self.checkString = '' #use this for string matching (partial match will do)
		#for pattern refer to: http://nbviewer.ipython.org/github/rasbt/python_reference/blob/master/tutorials/useful_regex.ipynb
		self.emailPattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

	
	def handle_starttag(self, tag, attrs):
		""" Set search string if tag + attriburte matces, searches for e-mail address in tags
		"""
		if tag == 'span' or tag == 'a':
			for atr in attrs:
				if atr[0] == 'href':
					if self.emailPattern.match(atr[1][7:]):
						self.addemail(atr[1][7:]) #parse only mailto: links
				elif atr[0] == 'id' and atr[1] == 'lblVrstaZaposlenja':
					#set search string	
					self.checkString = 'osposobljavanje'

	def handle_endtag(self, tag):
		pass

	def handle_data(self, data):
		""" React only to search string rendering page invalid if match is found
		"""
		if self.checkString != '':
			if data.find(self.checkString) > -1:
				self.valid = False
			self.checkString = '' #reset search string		

		#next search all content for email address
		addresses = self.emailPattern.search(data)
		if addresses:
			self.addemail(addresses.group()) #add just first email address

	def addemail(self, address):
		if address not in self.targetMails:
			self.targetMails.append(address)
	

class ItemObject(threading.Thread):
	
#FIXME: create variables that are needed for multithreading and see what return values will be needed
	
	def __init__(self, url, title, configObj, workpath):
		threading.Thread.__init__(self)
		self.Sent = False
		self.cfg = configObj
		
		#user data and required configuration values
		try:
			self.UNAME, self.MYEMAIL, self.msgtemplate = self.cfg.Read('user', username=None, emailaddress=None, msgtemplate=None).values()
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
		#FIXME: transfer configuratiion somehow
		parseObj = DetailsPageParser()
		
		#try to retrive details page
		
		
		#check if email will be sent
		self.sendMessage()
	
	
	def runOLD(self):
		parseObj = DetailsPageParser()
		try:
			res = urllib.urlopen(self.url)
			parseObj.feed(res.read())
		except Exception as e:
			#print e
			pass

		#assign email addresse form parse objec regarldess will they be used or not
		self.targetMailList = parseObj.targetMails
		
		#now check if message can be sent
		if parseObj.valid and len(self.targetMailList) > 0:
			self.sent = self.sendMessage()
		

	def Results(self):
		""" Return list of resulst
		Send atempt result  GUID Title Listof addreesses
		"""
		return  self.sent, self.id, self.TITLE, self.url, ','.join(self.targetMailList)


	def sendMessage(self):
		
		#FIXME: pass type of the message
		#print len(self.targetEmailList)
		
		
		self.prepareApplyMessage()
		
		return False
		if not self.sendMail:
		#print "message sending disabled"
			return True

		#once again debug test, on my mail address
		#self.targetMailList = ['hrvoje@zlatnodoba.hr']

		if len(self.targetMailList) > 0:
			
			msgTXT = ""
			msgHTML = ""

			#forget best practices hardcode filename in here
			with open(self.scriptpath +  'msgtext.txt', 'r') as fp:
				for line in fp:
					msgTXT += self.putContent(line, False)
					msgHTML += self.putContent(line, True) 

			#print msgHTML
			#print msg
			
			msg = MIMEMultipart('alternative')
		 	msg['Subject'] = 'Javljanje na natjecaj ' + self.TITLE
			msg['From'] = 'Hrvoje Novosel<hnovosel@live.com>'	
			msg['To'] = ', '.join(self.targetMailList)

			if msgTXT != '':
				partTXT = MIMEText(msgTXT, 'plain')
				msg.attach(partTXT)			

			if msgHTML != '':
				partHTML = MIMEText(msgHTML, 'html')
				msg.attach(partHTML)

	
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

	def prepareApplyMessage(self):
		""" Prepeare regular message, for position application
		"""
		
		print self.msgtemplate
		
		
	def prepareHzzMessage(self):
		print 'prepare spectial hzz message'


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

	
