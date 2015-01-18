Hzz app
======================

This application was developed as an answer to the personal need for easy and automatic way of applying to the job position tenders. Application is in testing and early beta stage, this application will, according to the settings in configuration file go throughout job tenders from hzz's rss feed list and automatically send a job application e-mail message. Sample templates of e-mail messages can be found in res folder, although any text document can be used as e-mail message template. After first run application creates a log of tenders to which e-mail message was sent to ensuring that for no item message is sent more than once. If for any reason log files are moved or corrupted(edited) application may send more than one message for the same job tender.

As the main objective of this application has been achieved, depending on the usefulness and demand, further improvements of the code can be expected. To name some of them: proper filtering engine, detailed items classification, simple UI and huge usability improvements, better error handling and enabling attachment support for email messages. 

For any questions and technical support regarding this application you can contact me at hnnovose@live.com


Installation
------------
Extract downloaded tar.bz file or copy code form github into desired
folder and edit [configuration file](#config) before first run. 


Dependencies
------------
python 2.6

Application was tested using *nix systems, although it
should run under windows environment no tests were performed. Also,
for now utf-8 support under default Mac OS interpreter is limited and
some application parsing features will not work properly.


Usage examples
--------------
Application can be executed using cli, ex.:

```shell
python hzzapp.py
```

With a help from crond or similar service application can be executed constantly in specific time intervals (refer to crond man for cron syntax), ex:

```crontab
0 9-17 * * 1-6 python $HOME/hzzapp/hzzapp.py >> $HOME/hzzapp/logs/cronrun.log
```

Template messages
------------------

Available variables (case sensitive):

{TITLE}  Item title
{CVURL} URL of online C.V. version
{UNAME} User's full name
{url} URL of the items page


<a name="config">Configuration file</a>
------------------
Configuration file is composed of sections (flagged by square brackets) followed by name=value pairs (style of RFC 822)

- app
	* sentlog location of log with items to whom application did apply 
	* passedlog filename of log with items to which application did not apply 
	* logfilename filename of application execution log file
	* filterlist textual list of words that act as exclusion words based on their occurrence in the subject of the message
	* searchinterval interval in days to which application will search for items
	* output log/stdout/log|stdout enumeration for redirection of application's output. Value of log 

- hzz
	* urllist a comma separated list of hzz rss category list urls
	* osposobljavanja yes/no enumeration enabling filtration of job tenders of "Strucno osposobljavanje bez zasnivanja radnog odnosa", if set to yes application will skip them 

- generalmail
	* msgsubject message subject line for e-mail messages sent for job application
	* msgtemplate file name of the text file containing message text

- hzzspectial
	* enable 
	* msgsubject message subject line
	* msgtemplate file name of the text file containing message text

- smtp
	* server smtp server address
	* uname optional user name, if server requires authentication
	* pwd optional password, if server requires authentication
	* SSL yes/no enumeration indicating if server uses SSL connection

- user
	* username full name of the user
	* emailaddress valid e-mail address of the user
	* cvurl optional url to the online version of CV


License
-------
This application is a free software and you can redistribute and/or modify it under terms of GNU General Public License as published by the Free Software Fundation (http://www.gnu.org/copyleft/gpl.html)


Disclaimer
---------
This application is written and distributed with good intentions and in desire that someone will find it useful. However, it is distributed "AS IS" and without warranty of any kind. For any possible usage of this software you acknowledge and agree that the author makes no representation for the adequacy of this application for users needs, or that the application will be error free. Under no event arising in any way from usage of this software, author is liable for any direct, indirect, consequential or any other kind of damage (including, but not only limited to loss of profits or business interruption) regardless of its cause and on any theory of liability.



