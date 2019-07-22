#!/usr/bin/python
# PyPostSettings.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains the class responsible for managing settings for the post-processing portion of the script

import datetime
import time
import os
import PyPostTools

# PyPostSettings: Class responsible for obtaining information from the control file and parsing it to classes that need the information
class PyPostSettings(PyPostTools.Singleton):
	settings = {}
	logger = None
	
	initialized = False
	
	def loadSettings(self):
		curDir = os.path.dirname(os.path.abspath(__file__))
		controlFile = curDir + "python_post_control.txt"
		with open(controlFile) as f: 
			for line in f: 
				#To-Do: This can be simplified to a single if block, but for the time being, I'm going to leave it as is
				if line.split():
					tokenized = line.split()
					if(tokenized[0][0] != '#'):
						if(tokenized[1].find("[") != -1):
							#Array-like
							inStr = tokenized[1]
							insideSubStr = inStr[inStr.find("[")+1:inStr.find("]")]
							levels = insideSubStr.split(",")
							# Check for transformations
							if(inStr.find("(") != -1):
								transformType = inStr[inStr.find("(")+1:inStr.find(")")]
								if(transformType == "int"):
									tType = int
								elif(transformType == "float"):
									tType = float
								else:
									raise Exception("Invalid transformType passed to loadSettings, " + transformType + " is not valid")
								levels = list(map(tType, levels))
							self.settings[tokenized[0]] = levels
							#self.logger.write("Applying setting (" + tokenized[0] +", ARRAY-LIKE, TRANSFORM: " + transformType + "): " + str(levels))
						else:
							self.settings[tokenized[0]] = tokenized[1]
							#self.logger.write("Applying setting (" + tokenized[0] +"): " + tokenized[1])
		#Test for program critical settings
		if(not self.settings):
			self.logger.write("***FAIL*** Program critical variables missing, check for existence of python_post_control.txt, abort.")
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
     
	def __init__(self):
		self.logger = PyPostTools.pyPostLogger()
		if(not self.initialized):
			if(self.loadSettings() == False):
				logger.write("***FAIL*** Unable to init PyPostSettings(), python_post_control.txt not found")
				logger.close()
				sys.exit("Failed to load settings, please check for python_post_control.txt")
			self.initialized = True