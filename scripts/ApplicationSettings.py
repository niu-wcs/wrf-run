#!/usr/bin/python
# ApplicationSettings.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains the class responsible for managing settings for the application

import datetime
import time
import os
import Tools

# AppSettings: Class responsible for obtaining information from the control file and parsing it to classes that need the information
class AppSettings():
	startTime = ""
	endTime = ""
	runDays = 0
	runHours = 0
	settings = {}
	replacementKeys = {}
	myUserID = None
	logger = None
	
	def loadSettings(self):
		curDir = os.path.dirname(os.path.abspath(__file__))
		controlFile = curDir[:curDir.rfind('/')] + "/control.txt"
		with open(controlFile) as f: 
			for line in f: 
				#To-Do: This can be simplified to a single if block, but for the time being, I'm going to leave it as is
				if not line.split():
					#Comment
					self.logger.write("Ignored empty line")
				else:
					tokenized = line.split()
					if(tokenized[0][0] == '#'):
						#Comment line, ignore
						self.logger.write("Comment line: " + line)
					else:
						self.settings[tokenized[0]] = tokenized[1]
						self.logger.write("Applying setting (" + tokenized[0] +"): " + tokenized[1])
		#Test for program critical settings
		if(not self.settings):
			self.logger.write("Program critical variables missing, check for existence of control.txt, abort.")
			return False
		else:
			self.settings["headdir"] = curDir[:curDir.rfind('/')] + '/'
			return True
        
	def fetch(self, key):
		try:
			return self.settings[key]
		except KeyError:
			print("Key does not exist")
			return None    
			
	def assembleKeys(self):	
		# Construct the replacement dictionary from the settings
		self.replacementKeys["[run_days]"] = str(self.runDays)
		self.replacementKeys["[run_hours]"] = str(self.runHours)
		self.replacementKeys["[start_date]"] = str(self.startTime.strftime('%Y-%m-%d_%H:%M:%S'))
		self.replacementKeys["[end_date]"] = str(self.endTime.strftime('%Y-%m-%d_%H:%M:%S'))
		self.replacementKeys["[start_year]"] = str(self.startTime.year)
		self.replacementKeys["[start_month]"] = str(self.startTime.month)
		self.replacementKeys["[start_day]"] = str(self.startTime.day)
		self.replacementKeys["[start_hour]"] = str(self.startTime.hour)
		self.replacementKeys["[end_year]"] = str(self.endTime.year)
		self.replacementKeys["[end_month]"] = str(self.endTime.month)
		self.replacementKeys["[end_day]"] = str(self.endTime.day)
		self.replacementKeys["[end_hour]"] = str(self.endTime.hour)
		self.replacementKeys["[wrf_module]"] = self.fetch("wrfmodule")
		self.replacementKeys["[geog_path]"] = self.fetch("geogdir")
		self.replacementKeys["[table_path]"] = self.fetch("tabledir")
		self.replacementKeys["[run_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8]
		self.replacementKeys["[out_geogrid_path]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_postprd_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/postprd"
		self.replacementKeys["[data_dir]"] = self.fetch("datadir") + '/' + self.fetch("modeldata") + '/' + self.fetch("starttime")
		self.replacementKeys["[num_geogrid_nodes]"] = self.fetch("num_geogrid_nodes")
		self.replacementKeys["[num_geogrid_processors]"] = self.fetch("num_geogrid_processors")
		self.replacementKeys["[geogrid_walltime]"] = self.fetch("geogrid_walltime")
		self.replacementKeys["[mpi_geogrid_total]"] = str(int(self.fetch("num_geogrid_nodes")) * int(self.fetch("num_geogrid_processors")))
		self.replacementKeys["[num_metgrid_nodes]"] = self.fetch("num_metgrid_nodes")
		self.replacementKeys["[num_metgrid_processors]"] = self.fetch("num_metgrid_processors")
		self.replacementKeys["[metgrid_walltime]"] = self.fetch("metgrid_walltime")
		self.replacementKeys["[mpi_metgrid_total]"] = str(int(self.fetch("num_metgrid_nodes")) * int(self.fetch("num_metgrid_processors")))
		self.replacementKeys["[num_real_nodes]"] = self.fetch("num_real_nodes")
		self.replacementKeys["[num_real_processors]"] = self.fetch("num_real_processors")
		self.replacementKeys["[real_walltime]"] = self.fetch("real_walltime")
		self.replacementKeys["[mpi_real_total]"] = str(int(self.fetch("num_real_nodes")) * int(self.fetch("num_real_processors")))	
		self.replacementKeys["[num_wrf_nodes]"] = self.fetch("num_wrf_nodes")
		self.replacementKeys["[num_wrf_processors]"] = self.fetch("num_wrf_processors")
		self.replacementKeys["[wrf_walltime]"] = self.fetch("wrf_walltime")
		self.replacementKeys["[mpi_wrf_total]"] = str(int(self.fetch("num_wrf_nodes")) * int(self.fetch("num_wrf_processors")))
		self.replacementKeys["[num_upp_nodes]"] = self.fetch("num_upp_nodes")
		self.replacementKeys["[num_upp_processors]"] = self.fetch("num_upp_processors")
		self.replacementKeys["[upp_walltime]"] = self.fetch("upp_walltime")
		self.replacementKeys["[mpi_upp_total]"] = str(int(self.fetch("num_upp_nodes")) * int(self.fetch("num_upp_processors")))	
	 
	def replace(self, inStr):
		if not inStr:
			return inStr
		fStr = inStr
		for key, value in self.replacementKeys.items():
			kStr = str(key)
			vStr = str(value)
			fStr = fStr.replace(kStr, vStr)
		return fStr
		
	def whoami(self):
		return self.myUserID
     
	def __init__(self):
		self.logger = Tools.loggedPrint.instance()	
	
		if(self.loadSettings() == False):
			logger.write("Cannot init program, control.txt not found")
			logger.close()
			sys.exit("Failed to load settings, please check for control.txt")
        
		self.myUserID = os.popen("whoami").read()
		
		self.startTime = datetime.datetime.strptime(self.fetch("starttime"), "%Y%m%d%H")
		self.runDays = self.fetch("rundays")
		self.runHours = self.fetch("runhours")

		self.endTime = self.startTime + datetime.timedelta(days=int(self.runDays), hours=int(self.runHours))

		self.assembleKeys()