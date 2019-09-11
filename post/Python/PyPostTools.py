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
import subprocess

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
	def __init__(self, command):
		runCmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		runCmd.wait()
		cResult, stderr = runCmd.communicate()
		cResult = str(cResult)
		stderr = str(stderr)
		self.stored = [cResult, stderr]
			
	def fetch(self):
		return self.stored		
		
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
		
def write_job_file(host, scheduler_port=None, project_name=None, queue=None, nodes=None, wall_time=None, nProcs=1):
	if(scheduler_port == None or project_name == None or queue == None or nodes == None or wall_time == None):
		return False
	with open("dask-worker.job", 'w') as target_file:
		target_file.write("#!/bin/bash" + '\n')
		target_file.write("#COBALT -t " + str(wall_time) + '\n')
		target_file.write("#COBALT -n " + str(nodes) + '\n')
		target_file.write("#COBALT -A " + str(project_name) + '\n')
		target_file.write("#COBALT -q " + str(queue) + '\n')
		target_file.write("#COBALT --attrs mcdram=cache:numa=quad" + '\n' + '\n')
		target_file.write("NODES=`cat $COBALT_NODEFILE | wc -l`" + '\n')
		target_file.write("PROCS=$((NODES * " + str(nProcs) + "))" + '\n' + '\n')
		target_file.write("for host in `uniq $COBALT_NODEFILE`; do" + '\n')
		target_file.write("   ssh $host launch-worker.sh &" + '\n')
		target_file.write("done" + '\n')
		target_file.write("sleep infinity")
	return True
	
def write_worker_file(host, scheduler_port=None, nProcs=1):
	if(scheduler_port == None):
		return False
	with open("launch-worker.sh", 'w') as target_file:
		target_file.write("#!/bin/bash" + '\n')
		target_file.write("/projects/climate_severe/Python/anaconda/bin/python3.7 -m distributed.cli.dask_worker \\" + '\n')
		target_file.write(str(host) + ":" + str(scheduler_port) + " --nprocs " + str(nProcs) + "\\" + '\n')
		target_file.write(" --death-timeout 120" + '\n\n')
	return True	