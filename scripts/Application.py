#!/usr/bin/python
# Application.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# The primary script file used by this process, handles the "fork" calls to the other classes and methods

import sys
import os
import datetime
import ApplicationSettings
import ModelData
import Cleanup
import Template
import Jobs
import Tools

# Application: Class responsible for running the program steps.
class Application():			
	def __init__(self):
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		logger = Tools.loggedPrint.instance()
	
		logger.write("Initializing WRF Auto-Run Program")
		#Step 1: Load program settings
		logger.write(" 1. Loading program settings, Performing pre-run directory creations and loading ANL modules")
		settings = ApplicationSettings.AppSettings()
		modelParms = ModelData.ModelDataParameters(settings.fetch("modeldata"))
		if not modelParms.validModel():
			sys.exit("Program failed at step 1, model data source: " + settings.fetch("modeldata") + ", is not defined in the program.")
		logger.write(" - Settings loaded, model data source " + settings.fetch("modeldata") + " applied to the program.")
		prc = Cleanup.PostRunCleanup(settings)
		prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = False, cleanModelData = False)
		mParms = modelParms.fetch()
		if(settings.fetch("run_prerunsteps") == '1'):
			Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8])
			Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8] + "/output")		
			Tools.popen(settings, "mkdir " + settings.fetch("wrfdir") + '/' + settings.fetch("starttime")[0:8] + "/postprd")
		else:
			logger.write(" 1. run_prerunsteps is turned off, directories have not been created")
		logger.write(" 1. Done.")
		#Step 2: Download Data Files
		logger.write(" 2. Downloading Model Data Files")
		modelData = ModelData.ModelData(settings, modelParms)
		if(settings.fetch("run_prerunsteps") == '1'):
			modelData.fetchFiles()
		else:
			logger.write(" 2. run_prerunsteps is turned off, model data has not been downloaded")
		logger.write(" 2. Done")
		#Step 3: Generate run files
		logger.write(" 3. Generating run files from templates")
		settings.add_replacementKey("[interval_seconds]", mParms["HourDelta"] * 60 * 60)
		tWrite = Template.Template_Writer(settings)
		if(settings.fetch("run_prerunsteps") == '1'):
			i = 0
			for ext in mParms["FileExtentions"]:
				tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/namelist.wps.template", "namelist.wps." + ext, extraKeys = {"[ungrib_prefix]": ext, "[fg_name]": mParms["FGExt"]})
				if(i == 0):
					Tools.popen(settings, "cp namelist.wps." + ext + " namelist.wps.geogrid")
				i += 1
			tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/namelist.input.template", "namelist.input")
			tWrite.generateTemplatedFile(settings.fetch("headdir") + "templates/wrf.job.template", "wrf.job")
		else:
			logger.write(" 3. run_prerunsteps is turned off, template files have not been created")
		logger.write(" 3. Done")
		#Step 4: Run the WRF steps
		logger.write(" 4. Run WRF Steps")
		jobs = Jobs.JobSteps(settings, modelParms)
		logger.write("  4.a. Checking for geogrid flag...")
		Tools.Process.instance().HoldUntilOpen(breakTime = 86400)
		if(settings.fetch("run_geogrid") == '1'):
			logger.write("  4.a. Geogrid flag is set, preparing geogrid job.")
			jobs.run_geogrid()
			logger.write("  4.a. Geogrid job Done")
		else:
			logger.write("  4.a. Geogrid flag is not set, skipping step")
		logger.write("  4.a. Done")
		logger.write("  4.b. Running pre-processing executables")
		Tools.Process.instance().HoldUntilOpen(breakTime = 86400)
		if(settings.fetch("run_preprocessing_jobs") == '1'):
			if(jobs.run_preprocessing() == False):
				logger.write("   4.b. Error in pre-processing jobs")
				logger.close()		
				sys.exit("   4.b. ERROR: Pre-processing jobs failed, check error logs")
		else:
			logger.write("  4.b. run_preprocessing_jobs is turned off, skiping this step")
		Tools.Process.instance().HoldUntilOpen(breakTime = 86400)
		logger.write("  4.b. Done")
		logger.write("  4.c. Running WRF Model")		
		if(settings.fetch("run_wrf") == '1'):
			if(jobs.run_wrf() == False):
				logger.write("   4.c. Error at WRF.exe")
				logger.close()		
				sys.exit("   4.c. ERROR: wrf.exe process failed to complete, check error file.")	
		else:
			logger.write("  4.c. run_wrf is turned off, skiping wrf.exe process")				
		logger.write("  4.c. Done")
		logger.write(" 4. Done")
		#Step 5: Run postprocessing steps
		if(settings.fetch("run_postprocessing") == '1'):
			logger.write(" 5. Running post-processing")
			post = Jobs.Postprocessing_Steps(settings, modelParms)
			Tools.Process.instance().HoldUntilOpen(breakTime = 86400)
			if(post.prepare_postprocessing() == False):
				logger.write("   5. Error initializing post-processing")
				logger.close()			
				sys.exit("   5. ERROR: post-processing process failed to initialize, check error file.")
			Tools.Process.instance().HoldUntilOpen(breakTime = 86400)
			if(post.run_postprocessing() == False):
				logger.write("   5. Error running post-processing")
				logger.close()				
				sys.exit("   5. ERROR: post-processing process failed to complete, check error file.")			
			logger.write(" 5. Done")
		else:
			logger.write(" 5. Post-processing flag disabled, skipping step")
		#Step 6: Cleanup
		logger.write(" 6. Cleaning Temporary Files")
		prc.performClean(cleanAll = False, cleanOutFiles = True, cleanErrorFiles = True, cleanInFiles = True, cleanWRFOut = False, cleanModelData = True)
		logger.write(" 6. Done")		
		#Done.
		logger.write("All Steps Completed.")
		logger.write("Program execution complete.")
		logger.close()

# Run the program.
if __name__ == "__main__":
	pInst = Application()