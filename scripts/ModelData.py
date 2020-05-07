#!/usr/bin/python
# ModelData.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains classes and methods responsible for managing various incoming model data sources

import datetime
import time
import os
import sys
from multiprocessing.pool import ThreadPool
import Tools
import ApplicationSettings

# ModelDataParameters: Mini class instance that stores information about various WRF data
class ModelDataParameters():
	dataParameters = {}
	model = ""
	
	def __init__(self, model):
		self.model = model
		self.dataParameters = {
			"CFSv2": {
				"VTable": ["Vtable.CFSv2.3D", "Vtable.CFSv2.FLX"],
				"FileExtentions": ["3D", "FLX"],
				"FGExt": "\'3D\', \'FLX\'",
				"HourDelta": 6,
				"ConstantsFile": "constant_file",
				"CanDownloadDirectly": True,
				"MetgridLevels": 30,
			},
			"NARR": {
				"VTable": ["Vtable.NARR"],
				"FileExtentions": ["NARR"],
				"FGExt": "NARR",
				"HourDelta": 3,
				"ConstantsFile": "NARR.constants",
				"CanDownloadDirectly": False,
				"MetgridLevels": 30,
			},
		}	
	
	def validModel(self):
		return self.model in self.dataParameters
	
	def fetch(self):
		return self.dataParameters[self.model]
		
#ModelData: Class responsible for downloading and managing model data
class ModelData():
	aSet = None
	modelParms = None
	startTime = ""
	dataDir = ""
	dataForecastHour = 0
	runDays = 1
	runHours = 1

	def __init__(self, settings, modelParms):
		self.aSet = settings
		self.modelParms = modelParms
		self.dataDir = settings.fetch("datadir") + '/' + settings.fetch("modeldata")
		self.startTime = datetime.datetime.strptime(settings.fetch("starttime"), "%Y%m%d%H")
		self.runDays = settings.fetch("rundays")
		self.runHours = settings.fetch("runhours")
		self.dataForecastHour = settings.fetch("modeldataforecasthour")
		logger = Tools.loggedPrint.instance()
		logger.write(" - Initializing model data with the following settings:")
		logger.write("  -> Model Data: " + settings.fetch("modeldata"))
		logger.write("  -> Model Data Forecast Hour: " + settings.fetch("modeldataforecasthour"))
		logger.write("  -> Data Directory: " + self.dataDir)
		logger.write("  -> Initialization Time: " + self.startTime.strftime('%Y%m%d%H'))
		logger.write("  -> Run Days: " + str(self.runDays))
		logger.write("  -> Run Hours: " + str(self.runHours))
		
	def fetchFiles(self):
		model = self.aSet.fetch("modeldata")
		mParms = self.modelParms.fetch()
		dirPath = self.dataDir + '/' + str(self.startTime.strftime('%Y%m%d%H'))
		logger = Tools.loggedPrint.instance()
		
		enddate = (self.startTime + datetime.timedelta(hours=int(self.dataForecastHour))) + datetime.timedelta(days=int(self.runDays), hours=int(self.runHours))
		dates = []
		current = (self.startTime + datetime.timedelta(hours=int(self.dataForecastHour)))
		while current <= enddate:
			dates.append(current)
			current += datetime.timedelta(hours=mParms["HourDelta"])	
			
		if(mParms["CanDownloadDirectly"] == True):
			if not os.path.isdir(dirPath):
				os.system("mkdir " + dirPath)	
				
			t = ThreadPool(processes=6)
			rs = t.map(self.pooled_download, dates)
			t.close()
		else:	
			if not os.path.isdir(dirPath):
				logger.write("  - Error: The selected data source does not support automatic downloading, and the data directory is not found.")
				logger.write("  - Please ensure the data is located in (" + dirPath + ") and try again.")
				sys.exit("")
			if not self.files_present(dates):
				logger.write("  - Error: Missing required input data to run WRF and the source does not allow automatic downloading, abort.")
				sys.exit("")
	
	def pooled_download(self, timeObject):
		model = self.aSet.fetch("modeldata")
		if(model == "CFSv2"):
			prs_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_pgbf/"
			flx_lnk = "https://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_6-hourly_9mon_flxf/"
			strTime = str(self.startTime.strftime('%Y%m%d%H'))
			
			pgrb2link = prs_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/pgbf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
			sgrb2link = flx_lnk + strTime[0:4] + '/' + strTime[0:6] + '/' + strTime[0:8] + '/' + strTime + "/flxf" + timeObject.strftime('%Y%m%d%H') + ".01." + strTime + ".grb2"
			pgrb2writ = self.dataDir + '/' + strTime + "/3D_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
			sgrb2writ = self.dataDir + '/' + strTime + "/flx_" + timeObject.strftime('%Y%m%d%H') + ".grb2"
			if not os.path.isfile(pgrb2writ):
				os.system("wget " + pgrb2link + " -O " + pgrb2writ)
			if not os.path.isfile(sgrb2writ):
				os.system("wget " + sgrb2link + " -O " + sgrb2writ)	
				
	def files_present(self, date_list):
		logger = Tools.loggedPrint.instance()
		model = self.aSet.fetch("modeldata")
		strTime = str(self.startTime.strftime('%Y%m%d%H'))
		allGood = True
		if(model == "CFSv2"):
			# This one auto-downloads
			pass
		elif(model == "NARR"):
			for oneDate in date_list:
				fPath = self.dataDir + '/' + strTime + "/merged_AWIP32." + oneDate.strftime('%Y%m%d%H')
				if not os.path.isfile(fPath):
					logger.write("  - Error: Missing expected input file (" + fPath + ").")
					allGood = False
		return allGood
			