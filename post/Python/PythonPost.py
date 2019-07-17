#!/usr/bin/python
# PythonPost.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This is the main python file called by the post-processing job and handles the parallel
#  processing on the wrfout files.

import os
import glob
from ..scripts import Tools
from netCDF4 import Dataset
import PyPostSettings
import Routines
import dask.array as da
from dask.array import map_blocks
from dask.distributed import Client, progress, metrics, LocalCluster

class PythonPost:
	dask_client = None
	dask_nodes = 0
	dask_threads = 0
	
	def __init__(self):
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		logger = Tools.loggedPrint.instance()
	
		logger.write("Initializing WRF Python Post-Processing Program")
		#Step 1: Load program settings
		logger.write(" 1. Application Initalization")
		logger.write("  - Loading control file, python_post_control.txt")
		pySet = PyPostSettings.PyPostSettings()
		logger.write("  - Success!")
		logger.write("  - Testing Environmental Variables")
		try:
			nodes = os.environ["PYTHON_POST_NODES"]
			threads = os.environ["PYTHON_POST_THREADS"]			
			self.dask_nodes = nodes
			self.dask_threads = threads		
		except KeyError:
			logger.write("KeyError encountered while trying to access important environmental variables, abort.")
			sys.exit("")
		logger.write("  - Success!")
		logger.write("  - Initializing Dask Client (" + self.dask_nodes + " Nodes Requested)")
		cluster = LocalCluster(n_workers=self.dask_nodes)
		self.dask_client = Client(cluster)
		routines = Routines.Routines(pySet, self.dask_client)
		logger.write("  - Success!")
		logger.write(" 1. Done.")
		logger.write(" 2. Post-Processing Calculations")
		routines.start_calculations()
		logger.write(" 2. Done.")
		logger.write(" 3. Generating Figures")
		routines.start_plotting()
		logger.write(" 3. Done.")
		logger.write(" 4. Final Steps")
		
		logger.write(" 4. Done.")
		logger.write("All Steps Completed.")
		logger.write("Program execution complete.")
		logger.close()		
		
# Run the program.
if __name__ == "__main__":
	pInst = PythonPost()