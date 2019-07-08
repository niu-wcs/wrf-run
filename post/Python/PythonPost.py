#!/usr/bin/python
# PythonPost.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This is the main python file called by the post-processing job and handles the parallel
#  processing on the wrfout files.

import glob
from ..scripts import Tools
from netCDF4 import Dataset

class PythonPost:

	def __init__(self):
		#empty
		
# Run the program.
if __name__ == "__main__":
	pInst = PythonPost()