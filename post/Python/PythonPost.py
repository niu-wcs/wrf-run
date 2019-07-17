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

class PythonPost:

	def __init__(self):
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		logger = Tools.loggedPrint.instance()
	
		logger.write("Initializing WRF Python Post-Processing Program")
		#Step 1: Load program settings
		logger.write(" 1. Loading settings")
		pySet = PyPostSettings.PyPostSettings()
		routines = Routines.Routines(pySet)
		logger.write(" 1. Done.")
		logger.write(" 2. Calculations")
		routines.start_calculations()
		logger.write(" 2. Done.")
		logger.write(" 3. Plotting")
		
		logger.write(" 3. Done.")
		logger.write(" 4. Final Steps")
		
		logger.write(" 4. Done.")
		logger.write("All Steps Completed.")
		logger.write("Program execution complete.")
		logger.close()		
		
# Run the program.
if __name__ == "__main__":
	pInst = PythonPost()