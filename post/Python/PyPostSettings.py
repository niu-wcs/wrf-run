#!/usr/bin/python
# PyPostSettings.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains the class responsible for managing settings for the post-processing portion of the script

import datetime
import time
import os
from ..scripts import Tools

# PyPostSettings: Class responsible for obtaining information from the control file and parsing it to classes that need the information
class PyPostSettings():
	settings = {}
	logger = None
	
	def loadSettings(self):
		curDir = os.path.dirname(os.path.abspath(__file__))
		controlFile = curDir[:curDir.rfind('/')] + "/python_post_control.txt"
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
							self.logger.write("Applying setting (" + tokenized[0] +", ARRAY-LIKE, TRANSFORM: " + transformType + "): " + str(levels))
						else:
							self.settings[tokenized[0]] = tokenized[1]
							self.logger.write("Applying setting (" + tokenized[0] +"): " + tokenized[1])
		#Test for program critical settings
		if(not self.settings):
			self.logger.write("Program critical variables missing, check for existence of python_post_control.txt, abort.")
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
		self.logger = Tools.loggedPrint.instance()	
	
		if(self.loadSettings() == False):
			logger.write("Unable to init PyPostSettings(), python_post_control.txt not found")
			logger.close()
			sys.exit("Failed to load settings, please check for python_post_control.txt")