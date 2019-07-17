#!/usr/bin/python
# PreparePyJob.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance is responsible for preparing the post-processing job file that submits the python scripts
#  to clusters

import glob
from ..scripts import Tools
from netCDF4 import Dataset

class PreparePyJob:
	aSet = None
	wrfOutDir = ""
	targetDir = ""
	logger = None

	#__init__: The class initialization instance, this requires a path containing the wrfout files and the target directory for output
	def __init__(self, settings, wrfOutDir, targetDir):
		self.aSet = settings
		self.wrfOutDir = wrfOutDir
		self.targetDir = targetDir
		self.logger = Tools.loggedPrint.instance()
		
	# prepare_job: This function writes the post-processing job file
	def prepare_job(self):
		Tools.Process.instance().Lock()	
		self.logger.write("  5.b. Entering prepare_job(), constructing job file.")
		fList = sorted(glob.glob(self.wrfOutDir + "/wrfout*"))
		fileCount = len(fList)
		out_job_contents = ""
		self.logger.write("  5.b. " + str(fileCount) + " wrfout files have been found.")
		if(fileCount > 0):
			Tools.popen(self.aSet, "export PYTHON_POST_DIR=" + self.wrfOutDir + '/')
			Tools.popen(self.aSet, "export PYTHON_POST_TARG_DIR=" + self.targetDir + '/')
			Tools.popen(self.aSet, "export PYTHON_POST_NODES=" + self.aSet.fetch("num_python_nodes"))
			Tools.popen(self.aSet, "export PYTHON_POST_THREADS=" + self.aSet.fetch("mpi_ranks_per_node"))
			Tools.popen(self.aSet, "export PYTHON_POST_FIRSTTIME=" + self.aSet.fetch("starttime"))