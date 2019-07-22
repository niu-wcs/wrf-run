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
import threading

# Thread-Safe Singleton: https://stackoverflow.com/questions/50566934/why-is-this-singleton-implementation-not-thread-safe
lock = threading.Lock()
def synchronized(lock):
    """ Synchronization decorator """
    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kw):
            with lock:
                return f(*args, **kw)
        return inner_wrapper
    return wrapper
		
class SingletonOptmized(type):
	_instances = {}
	def call(cls, *args, **kwargs):
		if cls not in cls._instances:
			with lock:
				if cls not in cls._instances:
					cls._instances[cls] = super(SingletonOptmizedOptmized, cls).call(*args, **kwargs)
		return cls._instances[cls]

class Singleton(metaclass=SingletonOptmized):
	pass
		
class pyPostLogger(Singleton):
	f = None
	filePath = None
	
	def __init__(self):
		curTime = datetime.date.today().strftime("%B%d%Y-%H%M%S")
		try:
			curDir = os.environ["PYTHON_POST_LOG_DIR"]
		except KeyError:
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