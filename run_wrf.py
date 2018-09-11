#!/usr/bin/python
# run_wrf.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Python script to execute the wrf_gaea.py script with options

import sys
import os
import datetime

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		curDir = os.path.dirname(os.path.abspath(__file__))
	
		#NOTE: If you're looking to automate (CRON) jobs, use this portion of the code to update control.txt
		
		#Run the script
		os.system("nohup " + curDir + "/scripts/Application.py")

if __name__ == "__main__":
	pInst = Application()