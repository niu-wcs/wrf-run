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
			print("Key (" + str(key) + ") does not exist")
			return None    
			
	def add_replacementKey(self, key, value):
		self.replacementKeys[key] = value
		self.logger.write("Additional replacement key added: " + str(key) + " = " + str(value))
			
	def assembleKeys(self):	
		# General replacement keys
		self.replacementKeys["[source_file]"] = self.fetch("sourcefile")
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
		self.replacementKeys["[geog_path]"] = self.fetch("geogdir")
		try:
			self.replacementKeys["[geogrid_table_path]"] = self.settings["tabledir"]
			self.replacementKeys["[metgrid_table_path]"] = self.settings["tabledir"]
		except KeyError:
			self.replacementKeys["[geogrid_table_path]"] = self.fetch("wpsdirectory") + "/geogrid"
			self.replacementKeys["[metgrid_table_path]"] = self.fetch("wpsdirectory") + "/metgrid"		
		self.replacementKeys["[run_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8]
		self.replacementKeys["[out_geogrid_path]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/output"
		self.replacementKeys["[run_postprd_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/postprd"
		self.replacementKeys["[data_dir]"] = self.fetch("datadir") + '/' + self.fetch("modeldata") + '/' + self.fetch("starttime")
		self.replacementKeys["[wrfout_output_dir]"] = self.fetch("wrfdir") + '/' + self.fetch("starttime")[0:8] + "/wrfout"
		# Keys for templated job files
		self.replacementKeys["[num_geogrid_nodes]"] = self.fetch("num_geogrid_nodes")
		self.replacementKeys["[geogrid_walltime]"] = self.fetch("geogrid_walltime")
		self.replacementKeys["[num_wrf_nodes]"] = self.fetch("num_wrf_nodes")
		self.replacementKeys["[wrf_walltime]"] = self.fetch("wrf_walltime")
		self.replacementKeys["[num_upp_nodes]"] = self.fetch("num_upp_nodes")
		self.replacementKeys["[upp_walltime]"] = self.fetch("upp_walltime")
		self.replacementKeys["[wrf_nio_tasks_per_group]"] = self.fetch("wrf_nio_tasks_per_group")
		self.replacementKeys["[wrf_nio_groups]"] = self.fetch("wrf_nio_groups")
		self.replacementKeys["[wrf_numtiles]"] = self.fetch("wrf_numtiles")
		self.replacementKeys["[wrf_mpi_ranks_per_node]"] = self.fetch("wrf_mpi_ranks_per_node")
		self.replacementKeys["[lfs_stripe_count]"] = self.fetch("lfs_stripe_count")
		# Keys for the namelist.input parameters
		self.replacementKeys["[wrf_debug_level]"] = self.fetch("wrf_debug_level")
		self.replacementKeys["[e_we]"] = self.fetch("e_we")
		self.replacementKeys["[e_sn]"] = self.fetch("e_sn")
		self.replacementKeys["[e_vert]"] = self.fetch("e_vert")
		self.replacementKeys["[geog_data_res]"] = self.fetch("geog_data_res")
		self.replacementKeys["[dx_y]"] = self.fetch("dx_y")
		self.replacementKeys["[map_proj]"] = self.fetch("map_proj")
		self.replacementKeys["[ref_lat]"] = self.fetch("ref_lat")
		self.replacementKeys["[ref_lon]"] = self.fetch("ref_lon")
		self.replacementKeys["[truelat1]"] = self.fetch("truelat1")
		self.replacementKeys["[truelat2]"] = self.fetch("truelat2")
		self.replacementKeys["[stand_lon]"] = self.fetch("stand_lon")
		self.replacementKeys["[p_top_requested]"] = self.fetch("p_top_requested")
		# self.replacementKeys["[num_metgrid_levels]"] = self.fetch("num_metgrid_levels")         #RF: Now handled by ModelData
		self.replacementKeys["[num_metgrid_soil_levels]"] = self.fetch("num_metgrid_soil_levels")
		self.replacementKeys["[mp_physics]"] = self.fetch("mp_physics")
		self.replacementKeys["[ra_lw_physics]"] = self.fetch("ra_lw_physics")
		self.replacementKeys["[ra_sw_physics]"] = self.fetch("ra_sw_physics")
		self.replacementKeys["[radt]"] = self.fetch("radt")
		self.replacementKeys["[sf_sfclay_physics]"] = self.fetch("sf_sfclay_physics")
		self.replacementKeys["[sf_surface_physics]"] = self.fetch("sf_surface_physics")
		self.replacementKeys["[bl_pbl_physics]"] = self.fetch("bl_pbl_physics")
		self.replacementKeys["[bldt]"] = self.fetch("bldt")
		self.replacementKeys["[cu_physics]"] = self.fetch("cu_physics")
		self.replacementKeys["[cudt]"] = self.fetch("cudt")
		self.replacementKeys["[num_soil_layers]"] = self.fetch("num_soil_layers")
		self.replacementKeys["[num_land_cat]"] = self.fetch("num_land_cat") 
		self.replacementKeys["[sf_urban_physics]"] = self.fetch("sf_urban_physics")
		self.replacementKeys["[hail_opt]"] = self.fetch("hail_opt")
		self.replacementKeys["[prec_acc_dt]"] = self.fetch("prec_acc_dt")
		self.replacementKeys["[io_vars]"] = "iofields_filename                   = 'IO_VARS.txt',\n" if self.fetch("use_io_vars") == "1" else ""
	 
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