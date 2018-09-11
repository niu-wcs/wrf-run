#!/usr/bin/python
# Wait.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains methods used to hold the process until specific conditions are met

import datetime
import time
import sys
import os
import subprocess
import Tools

#TimeExpiredException: Custom exception that is thrown when the Wait() command expires
class TimeExpiredException(Exception):
	pass
					
# Wait: Class instance designed to establish a hold condition until execution has been completed
class Wait:
	holds = []
	currentTime = ""
	abortTime = ""
	timeDelay = ""
	
	def __init__(self, holdList, abortTime = None, timeDelay=10):
		self.holds = holdList
		self.currentTime = datetime.datetime.utcnow()
		self.abortTime = self.currentTime + datetime.timedelta(days=int(999))
		self.timeDelay = timeDelay
		if(abortTime != None):
			self.abortTime = self.currentTime + datetime.timedelta(seconds=int(abortTime))
	
	def hold(self):
		cTime = datetime.datetime.utcnow()
		while cTime < self.abortTime:
			for indHold in self.holds:
				command = indHold["waitCommand"]
				retCode = indHold["retCode"]
				#cResult = os.popen(command).read()
				
				runCmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				runCmd.wait()
				cResult, stderr = runCmd.communicate()
				cResult = str(cResult)
				stderr = str(stderr)
				
				if 'splitFirst' in indHold:
					cResult = cResult.split()[0]
				if 'contains' in indHold:
					contains = indHold["contains"]
					if(contains in cResult):
						return retCode
				elif 'isValue' in indHold:
					isValue = indHold["isValue"]
					if(cResult == isValue):
						return retCode
				elif 'isNotValue' in indHold:
					isValue = indHold["isNotValue"]
					if(cResult != isValue):
						return retCode
				else:
					return cResult	
			time.sleep(self.timeDelay)
			cTime = datetime.datetime.utcnow()
		raise TimeExpiredException
		return None