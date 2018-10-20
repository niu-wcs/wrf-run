#!/usr/bin/python
# Jobs.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Script file containing classes and methods pertaining to the various jobs in the WRF processes

import sys
import os
import os.path
import datetime
import glob
import time
from multiprocessing.pool import ThreadPool
import ApplicationSettings
import ModelData
import Tools
import Wait
import Template

# JobSteps: Class responsible for handling the steps that involve job submission and checkup
class JobSteps:
	logger = None
	aSet = None
	modelParms = None
	startTime = ""
	dataDir = ""
	wrfDir = ""

	def __init__(self, settings, modelParms):
		self.aSet = settings
		self.logger = Tools.loggedPrint.instance()
		self.modelParms = modelParms
		self.dataDir = settings.fetch("datadir") + '/' + settings.fetch("modeldata")
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		# Copy important files to the directory
		Tools.popen(self.aSet, "cp " + settings.fetch("headdir") + "run_files/* " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		# Move the generated files to the run directory		
		Tools.popen(self.aSet, "mv namelist.input " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		Tools.popen(self.aSet, "mv geogrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv metgrid.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv real.job " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv wrf.job " + self.wrfDir + '/' + self.startTime[0:8])
		# Copy executables to the correct path
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("wpsexecutables") + "geogrid.exe " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("wpsexecutables") + "ungrib.exe " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("wpsexecutables") + "metgrid.exe " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("wrfexecutables") + "real.exe " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("wrfexecutables") + "wrf.exe " + self.wrfDir + '/' + self.startTime[0:8] + "/output")
	
	def run_geogrid(self):
		Tools.Process.instance().Lock()
		self.logger.write("run_geogrid(): Enter")
		Tools.popen(self.aSet, "mv namelist.wps.geogrid " + self.wrfDir + '/' + self.startTime[0:8] + "/namelist.wps")
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			Tools.popen(self.aSet, "chmod +x geogrid.job")
			Tools.popen(self.aSet, "qsub geogrid.job -q debug-cache-quad -t " + str(self.aSet.fetch("geogrid_walltime")) + " -n " + str(self.aSet.fetch("num_geogrid_nodes")) + " --mode script")
		self.logger.write("run_geogrid(): Exit")
		Tools.Process.instance().Unlock()
	
	def run_ungrib(self):	
		#ungrib.exe needs to run in the data directory
		Tools.Process.instance().Lock()
		self.logger.write("run_ungrib(): Enter")
		Tools.popen(self.aSet, "cp " + self.aSet.fetch("headdir") + "vtables/Vtable." + self.aSet.fetch("modeldata") + "* " + self.wrfDir + '/' + self.startTime[0:8])
		Tools.popen(self.aSet, "mv namelist.wps* " + self.wrfDir + '/' + self.startTime[0:8])
		mParms = self.modelParms.fetch()
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			with open("ungrib.csh", 'w') as target_file:
				target_file.write("cd " + self.wrfDir + '/' + self.startTime[0:8] + '\n')
				target_file.write("link_grib.csh " + self.dataDir + '/' + self.startTime + '/' + '\n')
				i = 0
				for ext in mParms["FileExtentions"]:
					target_file.write("cp " + mParms["VTable"][i] + " Vtable" + '\n')
					target_file.write("cp namelist.wps." + ext + " namelist.wps" + '\n')
					target_file.write("./ungrib.exe" + '\n')
					i += 1
			Tools.popen(self.aSet, "chmod +x ungrib.csh")
			Tools.popen(self.aSet, "./ungrib.csh")
		self.logger.write("run_ungrib(): Exit")
		Tools.Process.instance().Unlock()
		
	def run_metgrid(self):
		Tools.Process.instance().Lock()
		self.logger.write("run_metgrid(): Enter")
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):	
			Tools.popen(self.aSet, "chmod +x metgrid.job")		
			Tools.popen(self.aSet, "qsub metgrid.job -q debug-cache-quad -t " + str(self.aSet.fetch("metgrid_walltime")) + " -n " + str(self.aSet.fetch("num_metgrid_nodes")) + " --mode script")
			if(self.aSet.fetch("debugmode") == '1'):
				self.logger.write("Debug mode is active, skipping")
				Tools.Process.instance().Unlock()
				return True
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls metgrid.log* && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait.Wait(firstWait, timeDelay = 25)
				wait1.hold()
			except Wait.TimeExpiredException:
				sys.exit("metgrid.exe job not completed, abort.")
			#Now wait for the output file to be completed
			try:
				secondWait = [{"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "Successful completion of program metgrid.exe", "retCode": 1},
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 3 metgrid.log.0000", "contains": "error", "retCode": 2},]
				wait2 = Wait.Wait(secondWait, timeDelay = 25)
				wRC = wait2.hold()
				if wRC == 1:
					self.logger.write("run_metgrid(): Exit")
					Tools.Process.instance().Unlock()
					return True
				elif wRC == 2:
					self.logger.write("run_metgrid(): Exit (Failed, Code 2)")
					Tools.Process.instance().Unlock()
					return False
			except Wait.TimeExpiredException:
				sys.exit("metgrid.exe job not completed, abort.")
		self.logger.write("run_metgrid(): Failed to enter run directory")
		Tools.Process.instance().Unlock()
		return False
		
	def run_real(self):
		Tools.Process.instance().Lock()
		self.logger.write("run_real(): Enter")
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			Tools.popen(self.aSet, "chmod +x real.job")		
			Tools.popen(self.aSet, "qsub real.job -q debug-cache-quad -t " + str(self.aSet.fetch("real_walltime")) + " -n " + str(self.aSet.fetch("num_real_nodes")) + " --mode script")
			if(self.aSet.fetch("debugmode") == '1'):
				self.logger.write("Debug mode is active, skipping")
				Tools.Process.instance().Unlock()
				return True			
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls output/rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait.Wait(firstWait, timeDelay = 25)
				wait1.hold()			
			except Wait.TimeExpiredException:
				sys.exit("real.exe job not completed, abort.")
			#Now wait for the output file to be completed
			try:
				secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS", "retCode": 1},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
				wait2 = Wait.Wait(secondWait, timeDelay = 60)
				wRC = wait2.hold()
				if wRC == 2:
					self.logger.write("run_real(): Exit (Failed, Code 2)")
					Tools.Process.instance().Unlock()
					return False
				else:
					#Validate the presense of the two files.
					file1 = os.popen("(ls output/wrfinput_d01 && echo \"yes\") || echo \"no\"").read()
					file2 = os.popen("(ls output/wrfbdy_d01 && echo \"yes\") || echo \"no\"").read()
					if("yes" in file1 and "yes" in file2):
						self.logger.write("run_real(): Exit")
						Tools.Process.instance().Unlock()
						return True
					self.logger.write("run_real(): Exit (Failed, did not find wrfinput_d01 and wrfbdy_d01")
					Tools.Process.instance().Unlock()
					return False					
			except Wait.TimeExpiredException:
				sys.exit("real.exe job not completed, abort.")		
		self.logger.write("run_real(): Failed to enter run directory")
		Tools.Process.instance().Unlock()
		return False			
		
	def run_wrf(self):
		Tools.Process.instance().Lock()
		self.logger.write("run_wrf(): Enter")
		with Tools.cd(self.wrfDir + '/' + self.startTime[0:8]):
			# Do a quick file check to ensure wrf can run
			file1 = os.popen("(ls output/wrfinput_d01 && echo \"yes\") || echo \"no\"").read()
			file2 = os.popen("(ls output/wrfbdy_d01 && echo \"yes\") || echo \"no\"").read()
			if(not ("yes" in file1 and "yes" in file2) and (not self.aSet.fetch("debugmode") == '1')):
				self.logger.write("run_wrf(): Exit (Failed, cannot run wrf.exe without wrfinput_d01 and wrfbdy_d01)")
				Tools.Process.instance().Unlock()
				return False
			# Remove the old log files as these are no longer needed
			Tools.popen(self.aSet, "rm output/rsl.out.*")
			Tools.popen(self.aSet, "rm output/rsl.error.*")	
			Tools.popen(self.aSet, "chmod +x wrf.job")			
			Tools.popen(self.aSet, "qsub wrf.job -t " + str(self.aSet.fetch("wrf_walltime")) + " -n " + str(self.aSet.fetch("num_wrf_nodes")) + " --mode script")
			if(self.aSet.fetch("debugmode") == '1'):
				self.logger.write("Debug mode is active, skipping")
				Tools.Process.instance().Unlock()
				return True			
			#Submit a wait condition for the file to appear
			try:
				firstWait = [{"waitCommand": "(ls output/rsl.out.0000 && echo \"yes\") || echo \"no\"", "contains": "yes", "retCode": 1}]
				wait1 = Wait.Wait(firstWait, timeDelay = 25)
				wait1.hold()			
			except Wait.TimeExpiredException:
				sys.exit("wrf.exe job not completed, abort.")
			#Now wait for the output file to be completed (Note: Allow 7 days from the output file first appearing to run)
			try:
				secondWait = [{"waitCommand": "tail -n 1 output/rsl.out.0000", "contains": "SUCCESS COMPLETE WRF", "retCode": 1},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "fatal", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "runtime", "retCode": 2},
							  {"waitCommand": "tail -n 1 output/rsl.error.0000", "contains": "error", "retCode": 2},]
				# Note: I have the script checking the files once every three minutes so we don't stack five calls rapidly, this can be modified later if needed.
				wait2 = Wait.Wait(secondWait, timeDelay = 180)
				wRC = wait2.hold()
				if wRC == 2:
					self.logger.write("run_wrf(): Exit (Failed, Code 2)")
					Tools.Process.instance().Unlock()
					return False
				else:
					self.logger.write("run_wrf(): Exit")
					Tools.Process.instance().Unlock()
					return True				
			except Wait.TimeExpiredException:
				sys.exit("wrf.exe job not completed, abort.")				
		self.logger.write("run_wrf(): Failed to enter run directory")
		Tools.Process.instance().Unlock()
		return False			

class Postprocessing_Steps:
	aSet = None
	modelParms = None
	logger = None
	startTime = ""
	wrfDir = ""

	def __init__(self, settings, modelParms):
		self.aSet = settings
		self.logger = Tools.loggedPrint.instance()
		self.modelParms = modelParms
		self.wrfDir = settings.fetch("wrfdir")
		self.startTime = settings.fetch("starttime")
		self.postDir = self.wrfDir + '/' + self.startTime[0:8] + "/postprd/"
		
	# This method is mainly used for UPP post-processing as it requires some links to be established prior to running a Unipost.exe job. Python is skipped
	def prepare_postprocessing(self):
		Tools.Process.instance().Lock()
		if(self.aSet.fetch("post_run_unipost") == '1'):
			self.logger.write("  5.a. UPP Flagged Active")
			uppDir = self.aSet.fetch("headdir") + "post/UPP/"
			if(self.aSet.fetch("unipost_out") == "grib"):
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/wrf_cntrl.parm " + self.postDir + "wrf_cntrl.parm")
			elif(self.aSet.fetch("unipost_out") == "grib2"):
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/postcntrl.xml " + self.postDir + "postcntrl.xml")
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/postxconfig-NT.txt " + self.postDir + "postxconfig-NT.txt")
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/post_avblflds.xml " + self.postDir + "post_avblflds.xml")
				Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/params_grib2_tbl_new " + self.postDir + "params_grib2_tbl_new")
			else:
				self.logger.write("  5.a. Error: Neither GRIB or GRIB2 is defined for UPP output processing, please modify control.txt, aborting")
				Tools.Process.instance().Unlock()
				return False
			Tools.popen(self.aSet, "cp " + self.aSet.fetch("uppexecutables") + "unipost.exe " + self.postDir)
			Tools.popen(self.aSet, "ln -sf " + uppDir + "scripts/cbar.gs " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/nam_micro_lookup.dat " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "parm/hires_micro_lookup.dat " + self.postDir)
			Tools.popen(self.aSet, "ln -fs " + uppDir + "includes/*.bin " + self.postDir)
			self.logger.write("  5.a. Done")
			Tools.Process.instance().Unlock()
			return True
		elif(self.aSet.fetch("post_run_python") == '1'):
			self.logger.write("  5.a. Python Flagged Active")
			self.logger.write("  5.a. Done")
			Tools.Process.instance().Unlock()
			return True
		else:
			self.logger.write("  5. Error: No post-processing methods selected, please make changes to control.txt, aborting")
			Tools.Process.instance().Unlock()
			return False
			
	def run_postprocessing(self):
		if(self.aSet.fetch("post_run_unipost") == '1'):
			return self.run_postprocessing_upp()
		elif(self.aSet.fetch("post_run_python") == '1'):
			return True
		else:
			sys.exit("Error: run_postprocessing() called without a mode flagged, abort.")
			return False
		
	def run_postprocessing_upp(self):
		# We run unipost in a single job by assembling all of out wrfout files and writing the UPP steps into one file for each
		Tools.Process.instance().Lock()
		tWrite = Template.Template_Writer(self.aSet)
		curDir = os.path.dirname(os.path.abspath(__file__)) 
		temDir = self.aSet.fetch("headdir") + "templates/"
		uppDir = self.aSet.fetch("headdir") + "post/UPP/"
		fList = glob.glob(self.wrfDir + '/' + self.startTime[0:8] + "/output/wrfout*")
		fileCount = len(fList)
		fLogs = []
		self.logger.write("  5.b. Running UPP on " + str(fileCount) + " wrfout files")
		with Tools.cd(self.postDir):
			upp_job_contents = ""
			for iFile in fList:
				dNum = iFile[-23:-20]
				year = iFile[-19:-15]
				month = iFile[-14:-12]
				day = iFile[-11:-9]
				hour = iFile[-8:-6]
				minute = iFile[-5:-3]
				second = iFile[-2:]
				logName = "unipost_log_" + dNum + "_" + year + "_" + month + "_" + day + "_" + hour + ":" + minute + ":" + second + ".log"
				fLogs.append(logName)
				catCMD = ""
				if(self.aSet.fetch("unipost_out") == "grib"):
					catCMD = "cat > itag <<EOF\n" + iFile + '\n' + "netcdf\n" + str(year) + "-" + str(month) + "-" + str(day) + "_" + str(hour) + ":" + str(minute) + ":" + str(second) + '\n' + "NCAR\nEOF"
				elif(self.aSet.fetch("unipost_out") == "grib2"):
					catCMD = "cat > itag <<EOF\n" + iFile + '\n' + "netcdf\n" + "grib2\n" + str(year) + "-" + str(month) + "-" + str(day) + "_"  + str(hour) + ":" + str(minute) + ":" + str(second) + '\n' + "NCAR\nEOF"					
				else:
					#You should never end up here...
					sys.exit("  5.b. Error: grib/grib2 not defined in control.txt")
				upp_job_contents += catCMD
				upp_job_contents += '\n' + "rm fort.*"
				if(self.aSet.fetch("unipost_out") == "grib"):
					upp_job_contents += "\nln -sf " + uppDir + "parm/wrf_cntrl.parm fort.14"
				
				aprun = "aprun -n $n_mpi_ranks -N $n_mpi_ranks_per_node \\" + '\n'
				aprun += "--env OMP_NUM_THREADS=$n_openmp_threads_per_rank -cc depth \\" + '\n'
				aprun += "-d $n_hyperthreads_skipped_between_ranks \\" + '\n'
				aprun += "-j $n_hyperthreads_per_core \\" + '\n'
				aprun += "./unipost.exe > " + logName + '\n'
				aprun += "sleep 1\n"
				upp_job_contents += "\n" + aprun + '\n'
				
				aprun = ""
			# Create the job file, then submit it.
			tWrite.generateTemplatedFile(temDir + "upp.job.template", "upp.job", extraKeys = {"[upp_job_contents]": upp_job_contents})
			# Once the file has been written, submit the job.
			Tools.popen(self.aSet, "chmod +x upp.job")
			Tools.popen(self.aSet, "qsub upp.job -q debug-cache-quad -t " + str(self.aSet.fetch("upp_walltime")) + " -n " + str(self.aSet.fetch("num_upp_nodes")) + " --mode script")
			# Wait for all logs to flag as job complete
			for iFile in fLogs:
				try:
					wCond = [{"waitCommand": "tail -n 2 " + iFile, "contains": "PROGRAM UNIFIED_POST HAS ENDED", "retCode": 1},
							  {"waitCommand": "tail -n 3 " + iFile, "contains": "Primary job  terminated normally, but 1 process returned", "retCode": 2},]
					waitCond = Wait.Wait(wCond, timeDelay = 60)
					wRC = waitCond.hold()
					if wRC == 2:
						Tools.Process.instance().Unlock()
						return False			
				except Wait.TimeExpiredException:
					sys.exit("unipost.exe job not completed, abort.")
			# Run a quick ls -l test to ensure the number of files present matches what we're expecting
			fCountTest = Tools.popen(self.aSet, "ls -l WRFPRS*")
			cmdTxt = fCountTest.fetch()
			strCount = fCountTest[fCountTest.rfind('F'):]
			self.logger.write("  5.b. All UPP jobs completed (F" + int(strCount) + " found).")
			if(not (int(strCount)) == (fileCount - 1)):
				self.logger.write("  5.b. Error: Number of expected files (" + fileCount + ") does not match actual count (" + int(strCount) + 1 + ").")
				Tools.Process.instance().Unlock()
				return False
			# Now that we have our PRS files, we can convert those to CTL files
			self.logger.write("  5.b. Running GRIB to CTL process.")
			if(self.aSet.fetch("unipost_out") == "grib"):
				for fHour in range(0, fileCount):
					fStr = "0" + str(fHour) if fHour < 10 else str(fHour)
					inFile = "WRFPRS.GrbF" + fStr
					Tools.popen(self.aSet, uppDir + "scripts/grib2ctl.pl " + self.postDir + '/' + inFile + " > " + self.postDir + "/wrfprs_f" + fStr + ".ctl")
			elif(self.aSet.fetch("unipost_out") == "grib2"):
				for fHour in range(0, fileCount):
					fStr = "0" + str(fHour) if fHour < 10 else str(fHour)
					inFile = "WRFPRS.GrbF" + fStr
					Tools.popen(self.aSet, uppDir + "scripts/g2ctl.pl " + self.postDir + '/' + inFile + " > " + self.postDir + "/wrfprs_f" + fStr + ".ctl")
			#To-Do Note: Fork off to GrADS here...
			self.logger.write("  5.b. GRIB to CTL processes completed.")
			Tools.Process.instance().Unlock()
			return True