#!/usr/bin/python
# PythonPostProcessing.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# The head class instance for post-processing WRF using python

import Calculation
from ..scripts import Tools
from netCDF4 import Dataset
from wrf import getvar, ALL_TIMES, extract_vars, omp_set_num_threads, omp_get_max_threads

class PythonPostProcessing:
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
		
	# run_postprocessing_python: This function initializes the post-processing steps
	def run_postprocessing_python(self):
		Tools.Process.instance().Lock()	
		self.logger.write("  5.b. Entering run_postprocessing_python(), scanning for wrfout files.")
		fList = sorted(glob.glob(self.wrfOutDir + "/wrfout*"))
		fileCount = len(fList)
		upp_job_contents = ""
		self.logger.write("  5.b. " + str(fileCount) + " wrfout files have been found.")
		#wrfin = [Dataset(x) for x in fList]				