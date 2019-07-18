#!/usr/bin/python
# PyPostTools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains micro classes and methods used to help the program

import sys
import os
import os.path
import datetime
import time
		
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
class pyPostLogger:
	f = None
	filePath = None
	
	def __init__(self):
		curTime = datetime.date.today().strftime("%B%d%Y-%H%M%S")
		curDir = os.path.dirname(os.path.abspath(__file__)) 	
		logName = "pypost.log"	
		logFile = curDir + '/' + logName
		self.filePath = logFile
	
	def write(self, out):
		self.f = open(self.filePath, "a")
		self.f.write(out + '\n')
		self.f.close()
		print(out)
	
	def close(self):
		self.f.close()