#!/usr/bin/python
# PreparePyJob.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance is responsible for preparing the post-processing job file that submits the python scripts
#  to clusters

import glob
import Tools
import Wait

class PreparePyJob:
	aSet = None
	wrfOutDir = ""
	targetDir = ""
	logger = None

	#__init__: The class initialization instance, this requires a path containing the wrfout files and the target directory for output
	def __init__(self, settings, wrfOutDir, targetDir):
		self.aSet = settings
		self.wrfOutDir = wrfOutDir
		self.targetDir = targetDir
		self.logger = Tools.loggedPrint.instance()
		
	# prepare_job: This function writes the post-processing job file
	def prepare_job(self):
		Tools.Process.instance().Lock()	
		self.logger.write("  5.b. Entering prepare_job(), constructing job file.")
		fList = sorted(glob.glob(self.wrfOutDir + "/wrfout*"))
		fileCount = len(fList)
		out_job_contents = ""
		self.logger.write("  5.b. " + str(fileCount) + " wrfout files have been found.")
		if(fileCount <= 0):
			# Something went wrong.
			self.logger.write("  No files found, something is wrong, please check the output directory to ensure the wrfout* files are present.")
			return False
		out_job_contents += "#!/bin/bash\n"
		out_job_contents += "source " + self.aSet.fetch("sourcefile") + "\n"
		out_job_contents += "ulimit -s unlimited\n\n"
		
		out_job_contents += "export PYTHON_POST_DIR=" + self.wrfOutDir + "/\n"
		out_job_contents += "export PYTHON_POST_TARG_DIR=" + self.targetDir + "/\n"
		out_job_contents += "export PYTHON_POST_NODES=" + self.aSet.fetch("num_python_nodes") + "\n"
		out_job_contents += "export PYTHON_POST_THREADS=" + self.aSet.fetch("mpi_threads_per_rank") + "\n"
		out_job_contents += "export PYTHON_POST_FIRSTTIME=" + self.aSet.fetch("starttime") + "\n"
		out_job_contents += "export PYTHON_POST_LOG_DIR=" + self.targetDir + "/\n\n"
		
		out_job_contents += "cd " + self.aSet.fetch("postdir") + "/Python\n\n"
		
		out_job_contents += self.aSet.fetch("condainstallation") + " PythonPost.py&\n"
		out_job_contents += "PID_PyPost=$!\n"
		out_job_contents += "wait $PID_PyPost\n\n"
		
		with Tools.cd(self.targetDir):
			with open("python_post.job", 'w') as target_file:
				target_file.write(out_job_contents)		
			Tools.popen(self.aSet, "chmod +x python_post.job")
			self.logger.write("   -> Starting Python Post Processing Script, moving this script to holding pattern")
			jobSub = Tools.popen(self.aSet, "./python_post.job")	

			try:
				wCond = [{"waitCommand": "tail -n 3 pypost.log", "contains": "***SUCCESS***", "retCode": 1},
						 {"waitCommand": "tail -n 3 pypost.log", "contains": "***FAIL***", "retCode": 2}]
				waitCond = Wait.Wait(wCond, timeDelay = 60)
				wRC = waitCond.hold()			
				if wRC == 1:
					Tools.Process.instance().Unlock()
				elif wRC == 2:
					self.logger.write("PreparePyJob(): Exit (Failed at python, Code 2)")
					Tools.Process.instance().Unlock()
					return False					
			except Wait.TimeExpiredException:
				sys.exit("Python post processing job not completed, abort.")	
			return True