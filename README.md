# WRF on Gaea @ NIU #
## Dpt. Geographic & Atmospheric Sciences ##
## By: Robert C. Fritzen ##

### Introduction ###
This python script package automates the entire WRF process for use on cluster based computers, such as the Gaea computer provided for use by the Computer Science department at Northern Illinois University. This is a fully self-contained script package that handles the tasks of obtaining the data, running the pre-processing executables, the WRF process, and forking the task to post-processing scripts for visualization.

### Contents ###
This git repository contains the following subdirectories:
  * post: The folder containing the two post-processing methodologies used by this script.
    * UPP: The Unified Post-Processor 3.2 package scripts, support for both GRIB/GRIB2 to GrADS
	  * includes: A collection of the WRF binary files required to run the UPP process
	  * parm: Parameter files required by UPP
	  * scripts: Additional scripts needed for post-processing
	* Python: A plotting package based off of the wrf-python library
  * scripts: The python scripts used by this package
    * Application.py: The script package containing the execution path of the program
	* ApplicationSettings.py: Classes used to apply program settings via control.txt
	* Cleanup.py: Classes and methods used to clean output files and logs after program completion
	* Jobs.py: Classes and methods used to submit and monitor WRF jobs to clusters
	* Logging: Singleton class instance that handles logging the program process to a text file
	* ModelData.py: Classes and methods used to manage various data sources for the model
	* Template.py: Classes and methods used to modify and write template files
	* Tools.py: Extra classes and methods used as support tools for the program
	* Wait.py: Classes and methods used to hold the main thread until conditions are met
	* **__init__.py**: Empty text file used to define **scripts** as a module to be used by run_wrf.py
  * templates: Template text files for job scripts and namelist files used by WRF and jobs to be submitted to clusters, you should not edit these files.
  * vtables: WRF Vtable files for various model data sources, CFSv2 tables are included in this package.
In this directory:
  * run_wrf.py: The primary run process which runs Application.py in the background so execution via PuTTy can continue even after a session is disconnected
  * control.txt: A newline terminated text file that sets various parameters on the script (See below section on control.txt)
  * README.md: You're reading it!
  
Additionally, you will need to define a directory inside the repository directory called run_files, and place the following inside:
  * The WRF executables (wrf.exe, real.exe, tc.exe)
  * The WRF Run Files and Tables located in the /run/ folder of your WRF installation
  * If you are not planning on running the geogrid process (See run_geogrid below), place your geo_em file(s) in the same run files folder
  
### Control.txt ###
control.txt is a newline terminated text file which contains important parameters needed to run this script. The control.txt file MUST be located in the same directory as the run_wrf.py script file in order for the script to run. The format of this file is simple:

Each command line is split into two breaks:

**variable value**

EX: myvar 12

Would store the value of 12 in a parameter named myvar for the file. Any line that begins with a pound sign (#) is treated as a comment line. These variables are all defined in the AppSettings() class, but for simplicity, here is a list of the parameters accepted by control.txt

  * debugmode: Setting this variable to 1 will not run any commands, but instead print the commands to the console for debugging / testing purposes. Typically, leave this as 0.
  * starttime: The initialization time for the first forecast hour, the format is YYYYMMDDHH
  * rundays: The number of days to run the model after initialization
  * runhours: The number of hours to run in addition to rundays (IE: total = 24*rundays + runhours)
  * geogdir: The path to the wrf_geog/ folder stored on your machine
  * tabledir: The path to your shared WRF tables folder stored on your machine
  * datadir: The path to where you want GRIB data to be stored, the full path is: datadir/model source/YYYYMMDDHH/
  * wrfdir: The path to where you want model runs to occur on your machine
  * wrfmodule: The name of the WRF module on your cluster (Added via module add wrfmodule)
  * modeldata: The data source used in this run (*See the section below on adding model sources if you want to use something other than CFSv2*)
  * run_prerunsteps: A 1/0 flag used to designate if the pre-run steps, including symlinks and directory creations are needed. Typically, this is left as 1 unless debugging
  * run_geogrid: A 1/0 flag used to designate if the geogrid process needs to be run, if you are using the same grid space, run geogrid once and copy the resulting geo_em file to the run_files/ folder, then set the parameter to 0, otherwise geogrid will run.
  * run_ungrib: A 1/0 flag used to designate if the ungrib process needs to be run, only turn off if you are debugging a latter step
  * run_metgrid: A 1/0 flag used to designate if the metgrid process needs to be run, only turn off if you are debugging a latter step
  * run_real: A 1/0 flag used to designate if the real process needs to be run, only turn off if you are debugging a latter step
  * run_wrf: A 1/0 flag used to designate if the WRF process needs to be run, only turn off if you are debugging a latter step
  * num_geogrid_nodes: The number of CPU nodes to use in the geogrid process
  * num_geogrid_processors: The number of CPU processors to use in the geogrid process
  * geogrid_walltime: The maximum wall time to be required by the geogrid process
  * num_metgrid_nodes: The number of CPU nodes to use in the metgrid process
  * num_metgrid_processors: The number of CPU processors to use in the metgrid process
  * metgrid_walltime: The maximum wall time to be required by the metgrid process
  * num_real_nodes: The number of CPU nodes to use in the real.exe process
  * num_real_processors: The number of CPU processors to use in the real.exe process
  * real_walltime: The maximum wall time to be required by the real.exe process
  * num_wrf_nodes: The number of CPU nodes to use in the WRF process
  * num_wrf_processors: The number of CPU processors to use in the WRF process
  * wrf_walltime: The maximum wall time to be required by the WRF process 
  * run_postprocessing: This flag enables post-processing after the WRF run is completed. This package supports UPP and Python  
  * post_run_unipost: Set this flag to 1 if you wish to use UPP to post-process
  * post_run_python: Set this flag to 1 if you wish to use Python to post-process
  * unipost_out: A textual flag to indicate whether UPP should export to GRIB or GRIB2, the two choices are grib and grib2
  * num_upp_nodes: The number of CPU nodes to use in the UPP process
  * num_upp_processors: The number of CPU processors to use in the UPP process
  * upp_walltime: The maximum wall time to be required by the UPP process
  
### How to use this program ###
Once the entire script package is installed, you will need to define the WRF module that is used by your cluster system in the control.txt file, this is the wrfmodule variable. Then, you need to define the directory parameters (geogdir, tabledir, and wrfdir). By default, this script package is equipped to run WRF using CFSv2 data, however you may add other sources if you please (See the section below titled Adding Model Sources).

The run time parameters (starttime, rundays, runhours) need to be defined in the control.txt file, remember that runhours is in ADDITION to rundays, so keep that in mind when setting these parameters. You may adjust the nodes and processors settings as necessary, however these have been provided default values based on multiple tests such that you shouldn't have to. Once your control.txt file has been written you may run the python script **run_wrf.py** from the head directory to push the process to the background (Allowing you to safely close an SSH session and let the process completely run), or, if you want the output pushed to your SSH client, you may run **Application.py** in the scripts/ directory. All logging information will be saved to a log file in the scripts/ directory, and will be moved to a /logs/ folder upon script completion.
  
### Adding Model Sources ###
This script package was written for the CFSv2 forecast system as an input for the WRF model, however the script package is dynamic enough to allow for quick additions of other model sources.

First, you will need to obtain the VTable files for your specific model data source and include these in the directory.

Second, you'll need to add some basic model information to the *ModelDataParameters* class instance, located near the top of the scripts/ModelData.py file. A dictionary is contained in this class with the following format:
```python
			"CFSv2": {
				"VTable": ["Vtable.CFSv2.3D", "Vtable.CFSv2.FLX"],
				"FileExtentions": ["3D", "FLX"],
				"FGExt": "\'3D\', \'FLX\'",
				"HourDelta": 6,
			},
```
The name of the dictionary instance should ideally be the model data source. *VTable* is a list instance containing all VTable files contained in the head folder used by this model data source. *FileExtentions* is a list of all file extensions used by the incoming GRIB data, for specific models (IE: CFSv2), multiple files are needed, hence this allows it. *FGExt* is a parameter applied by namelist.wps for the extensions of the ungribbed files used by the metgrid process, make this similar to the GRIB files. Finally *HourDelta* is the amount of hours separating each incoming GRIB file.

Next, scroll down to the *ModelData* class and find the pooled_download section. You will need to incorporate an additional if/elif clause for your new model that downloads the model data, here is a sample:

```python
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
```

Finally, change the modeldata parameter in control.txt to match your model source.
				
### Contact Info ###
Any questions regarding the script package can be sent to Robert C. Fritzen (rfritzen1@niu.edu). In-person questions can be done from my office in Davis Hall, room 209.