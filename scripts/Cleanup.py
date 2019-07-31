#!/usr/bin/python
# Cleanup.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains classes used to handle post script run cleaning

import sys
import os
import ApplicationSettings
import Tools

class PostRunCleanup():
	sObj = None
	
	def __init__(self, settings):
		self.sObj = settings
		
	def performClean(self, cleanAll = True, cleanOutFiles = True, cleanErrorFiles = True, cleanBdyFiles = True, cleanInFiles = True, cleanWRFOut = True, cleanModelData = True):
		sTime = self.sObj.fetch("starttime")
		dataDir = self.sObj.fetch("datadir") + '/' + self.sObj.fetch("modeldata") + sTime
		wrfDir = self.sObj.fetch("wrfdir") + '/' + sTime[0:8]
		outDir = wrfDir + "/output"
		if(cleanAll == True):
			cleanOutFiles = True
			cleanErrorFiles = True
			cleanInFiles = True
			cleanWRFOut = True
			cleanModelData = True
		if(cleanOutFiles == True):
			Tools.popen(self.sObj, "rm " + wrfDir + "/geogrid.log.*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/metgrid.log.*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/ungrib.log*")
			Tools.popen(self.sObj, "rm " + outDir + "/rsl.out.*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/GEOGRID.o*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/METGRID.o*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/UNGRIB.o*") #This shouldn't be needed, but in the event we use a job for ungrib.
			Tools.popen(self.sObj, "rm " + outDir + "/REAL.o*")
			Tools.popen(self.sObj, "rm " + outDir + "/WRF.o*")
		if(cleanErrorFiles == True):
			Tools.popen(self.sObj, "rm " + outDir + "/rsl.error.*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/GEOGRID.e*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/METGRID.e*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/UNGRIB.e*") #This shouldn't be needed, but in the event we use a job for ungrib.
			Tools.popen(self.sObj, "rm " + outDir + "/REAL.e*")
			Tools.popen(self.sObj, "rm " + outDir + "/WRF.e*")	
		if(cleanBdyFiles == True):
			Tools.popen(self.sObj, "rm " + outDir + "/met_em*")
			Tools.popen(self.sObj, "rm " + outDir + "/wrfinput*")
			Tools.popen(self.sObj, "rm " + outDir + "/wrfbdy*")		
			Tools.popen(self.sObj, "rm " + outDir + "/geo_em.d01.nc*")
		if(cleanInFiles == True):
			Tools.popen(self.sObj, "rm " + wrfDir + "/GRIBFILE.*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/3D:*")
			Tools.popen(self.sObj, "rm " + wrfDir + "/FLX:*")
			Tools.popen(self.sObj, "rm " + outDir + "/FILE:*")
			Tools.popen(self.sObj, "rm " + outDir + "/aero*")
			Tools.popen(self.sObj, "rm " + outDir + "/bulk*")
			Tools.popen(self.sObj, "rm " + outDir + "/CAM*")
			Tools.popen(self.sObj, "rm " + outDir + "/capacity.asc")
			Tools.popen(self.sObj, "rm " + outDir + "/CCN*")
			Tools.popen(self.sObj, "rm " + outDir + "/CLM*")
			Tools.popen(self.sObj, "rm " + outDir + "/co2_trans")
			Tools.popen(self.sObj, "rm " + outDir + "/coeff*")
			Tools.popen(self.sObj, "rm " + outDir + "/constants.asc")
			Tools.popen(self.sObj, "rm " + outDir + "/create_p3_lookupTable_1.f90")
			Tools.popen(self.sObj, "rm " + outDir + "/ETA*")
			Tools.popen(self.sObj, "rm " + outDir + "/GEN*")
			Tools.popen(self.sObj, "rm " + outDir + "/grib*")
			Tools.popen(self.sObj, "rm " + outDir + "/kernels*")
			Tools.popen(self.sObj, "rm " + outDir + "/LANDUSE.TBL")
			Tools.popen(self.sObj, "rm " + outDir + "/masses.asc")
			Tools.popen(self.sObj, "rm " + outDir + "/MPTABLE.TBL")
			Tools.popen(self.sObj, "rm " + outDir + "/ozone*")
			Tools.popen(self.sObj, "rm " + outDir + "/p3_lookup_table_1.dat")
			Tools.popen(self.sObj, "rm " + outDir + "/RRTM*")
			Tools.popen(self.sObj, "rm " + outDir + "/RRTMG*")
			Tools.popen(self.sObj, "rm " + outDir + "/SOILPARM.TBL")
			Tools.popen(self.sObj, "rm " + outDir + "/termvels.asc")
			Tools.popen(self.sObj, "rm " + outDir + "/tr*")
			Tools.popen(self.sObj, "rm " + outDir + "/URB*")
			Tools.popen(self.sObj, "rm " + outDir + "/VEG*")
			Tools.popen(self.sObj, "rm " + outDir + "/wind-turbine-1.tbl")
			Tools.popen(self.sObj, "rm " + outDir + "/real.exe")
			Tools.popen(self.sObj, "rm " + outDir + "/tc.exe")
			Tools.popen(self.sObj, "rm " + outDir + "/wrf.exe")
		if(cleanWRFOut == True):
			Tools.popen(self.sObj, "rm " + outDir + "/wrfout*")
			Tools.popen(self.sObj, "rm " + outDir + "/wrfrst*")
		if(cleanModelData == True):
			Tools.popen(self.sObj, "rm -r " + dataDir)
		return None