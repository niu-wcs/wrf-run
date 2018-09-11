#!/usr/bin/python
# Template.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains methods used to modify and save the templated files

import ApplicationSettings

# Template_Writer: Class responsible for taking the template files and saving the use files with parameters set
class Template_Writer:
	aSet = None
	
	def __init__(self, settings):
		self.aSet = settings
					
	def generateTemplatedFile(self, inFile, outFile, extraKeys = None):
		inContents = []
		with open(inFile, 'r') as source_file:
			for line in source_file:
				inContents.append(line.strip())
		
		with open(outFile, 'w') as target_file:
			for line in inContents:
				newLine = line
				newLine = self.aSet.replace(newLine)
				if(extraKeys != None):
					for key, value in extraKeys.items():
						newLine = newLine.replace(key, value)
				newLine += '\n'
				target_file.write(newLine)	