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

def detect_ideal_processors(grid_x, grid_y, nodes, procs_per_node, wrf_io_groups, wrf_io_procs):
	smallest_x = grid_x / 10
	biggest_y_pair = 0

	smallest_x_io = smallest_x
	biggest_y_io = biggest_y_pair
	
	total_nodes = nodes * procs_per_node
	io_procs = wrf_io_groups * wrf_io_procs
	
	if io_procs == 0:
		found = False
		
		for i in range(1, (int)(grid_x / 10)+1):
			for j in range(1, (int)(grid_y / 10)+1):
				if(i * j == total_nodes):
					if((grid_x / i > 10) and (grid_y / j > 10)):
						if(i < smallest_x):
							smallest_x = i
							biggest_y_pair = j
						found = True
		if found:
			return ((smallest_x, biggest_y_pair))
		else:
			return None
	else:
		remaining = total_nodes - io_procs	

		found = False
		foundIO = False

		for i in range(1, (int)(grid_x / 10)+1):
			for j in range(1, (int)(grid_y / 10)+1):
				if(i * j == remaining):
					if((grid_x / i > 10) and (grid_y / j > 10)):
						if(i < smallest_x):
							smallest_x = i
							biggest_y_pair = j
							# Check for good IO
							if(biggest_y_pair % wrf_io_procs == 0):
								smallest_x_io = i
								biggest_y_io = j
								foundIO = True
						found = True
		if foundIO:
			return ((smallest_x_io, biggest_y_io))
		else:
			if found:
				return ((smallest_x, biggest_y_pair))
			else:
				return None

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
	storing = False

	def __init__(self, settings, command, storeOutput = True):
		self.storing = storeOutput
	
		if(settings.fetch("debugmode") == '1'):
			print("D: " + command)
		else:
			if storeOutput:
				runCmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				runCmd.wait()
				cResult, stderr = runCmd.communicate()
				cResult = str(cResult)
				stderr = str(stderr)
				self.stored = [cResult, stderr]
				loggedPrint.instance().write("popen(" + command + "): " + self.stored[0] + ", " + self.stored[1])
			else:
				runcmd = subprocess.Popen(command, shell=False, stdin=None, stdout=None, stderr=None)
				loggedPrint.instance().write("popen(" + command + "): Command fired with no return")
			
	def fetch(self):
		if not self.storing:
			return None
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