#!/usr/bin/python
# Tools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains micro classes and methods used to help the program

import sys
import os
import os.path
import datetime
import ApplicationSettings
import subprocess
import time

#CD: Current Directory management, see https://stackoverflow.com/a/13197763/7537290 for implementation. This is used to maintain the overall OS CWD while allowing embedded changes.
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
		
#popen: A wrapped call to the subprocess.popen method to test for the debugging flag.
class popen:
	def __init__(self, settings, command):
		if(settings.fetch("debugmode") == '1'):
			print("D: " + command)
		else:
			runCmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			runCmd.wait()
			cResult, stderr = runCmd.communicate()
			cResult = str(cResult)
			stderr = str(stderr)
			self.stored = [cResult, stderr]
			loggedPrint.instance().write("popen(" + command +"): \nSTORED[0]: " + self.stored[0] + "\nSTORED[1]: " + self.stored[1])
			
	def fetch(self):
		return self.stored
		
#singleton: Class decorator used to define classes as single instances across the program (See https://stackoverflow.com/questions/31875/is-there-a-simple-elegant-way-to-define-singletons)
class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
		
@Singleton
class loggedPrint:
	f = None
	filePath = None
	
	def __init__(self):
		curTime = datetime.date.today().strftime("%B%d%Y-%H%M%S")
		curDir = os.path.dirname(os.path.abspath(__file__)) 	
		logName = "wrf_run_script_" + str(curTime) + ".log"	
		logFile = curDir + '/' + logName
		self.filePath = logFile
	
	def write(self, out):
		self.f = open(self.filePath, "a")
		self.f.write(out + '\n')
		self.f.close()
		print(out)
	
	def close(self):
		self.f.close()
		
#BreakException: Custom exception that is thrown if the Process HoldUntilOpen() never completes
class BreakException(Exception):
	pass		
		
@Singleton
class Process:
	lock = False
	
	def __init__(self):
		self.lock = False
		
	def CanStart(self):
		return (self.lock == False)
		
	def HoldUntilOpen(self, breakTime = None):
		currentTime = datetime.datetime.utcnow()
		expTime = currentTime + datetime.timedelta(days=int(7))
		if(breakTime != None):
			expTime = currentTime + datetime.timedelta(seconds=int(breakTime))
		
		while(datetime.datetime.utcnow() < expTime):
			if(self.CanStart() == True):
				return True
			time.sleep(10)
		raise BreakException
		return False
		
	def Lock(self):
		self.lock = True
		
	def Unlock(self):
		self.lock = False