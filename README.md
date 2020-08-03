# WRF-Run #
## Dpt. Geographic & Atmospheric Sciences - [NIU WCS](https://wcs.niu.edu/) ##
## By: Robert C. Fritzen ##

### Introduction ###
This python script package automates the entire WRF process for use on cluster based computers. This is a fully self-contained script package that handles the tasks of obtaining the data, running the pre-processing executables, the WRF process, and forking the task to post-processing scripts for visualization.

This package has been tested on multiple environments with different scheduling systems, notes are shown below:
 * Argonne's Theta (COBALT): Fully Supported
 * Argonne's LCRC (SLURM): Fully Supported
 * NIU's Gaea (PBS): Limited Support
 
Systems listed as "Limited Support" are currently being worked on to bring it up to full support.

### Requirements ###
Included in this repository is a post-processing solution written in Python 3 as well as a UPP wrapper. If you want to use UPP, you may ignore this section, however, if you plan on using the Python module, you will need two other Python Packages to be installed:
  * wrf-python: https://github.com/NCAR/wrf-python
  * dask: https://github.com/dask/dask

### Contents ###
This git repository contains the following subdirectories:
  * post: The folder containing the two post-processing methodologies used by this script.
    * Python: A python based post-processing solution that uses wrf-python, dask, cartopy, and scipy. (See below section on python post processing)
	  * **__init.py**: Empty text file used to define the folder as a module
	  * ArrayTools.py: A set of wrf-python functions that have dask supported wrapper calls around them
	  * Calculation.py: A full suite of dask wrapped calls to wrf-python's fortran calculated fields, and method calls to obtain calculated variables
	  * ColorMaps.py: A set of color maps used for matplotlib figures
	  * Plotting.py: A set of functions used to generate figures of calbulated variables
	  * PyPostSettings.py: A class instance used to apply program settings from a control file.
	  * PyPostTools.py: A set of tools used by the other classes in this module
	  * PythonPost.py: The main script of the post-processing module, includes the main() call.
	  * **python_post_control.txt**: The control file for the post-processing module, please see the section below for more information.
	  * Routines.py: A wrapper class instance that collects information from the control file and parses it into a list of required function calls.
    * UPP: The Unified Post-Processor 3.2 package scripts, support for both GRIB/GRIB2 to GrADS
	  * includes: A collection of the WRF binary files required to run the UPP process
	  * parm: Parameter files required by UPP
	  * scripts: Additional scripts needed for post-processing
  * scripts: The python scripts used by this package
    * Application.py: The script package containing the execution path of the program
	* ApplicationSettings.py: Classes used to apply program settings via control.txt
	* Cleanup.py: Classes and methods used to clean output files and logs after program completion
	* Jobs.py: Classes and methods used to submit and monitor WRF jobs to clusters
	* Logging.py: Singleton class instance that handles logging the program process to a text file
	* ModelData.py: Classes and methods used to manage various data sources for the model
	* PreparePyJob.py: Class instance used to construct and monitor the Python Post-Processing job
	* Scheduler.py: Class definition for different job scheduler systems and the required bash flags and job script format
	* Template.py: Classes and methods used to modify and write template files
	* Tools.py: Extra classes and methods used as support tools for the program
	* Wait.py: Classes and methods used to hold the main thread until conditions are met
	* **__init__.py**: Empty text file used to define **scripts** as a module to be used by run_wrf.py
  * templates: Template text files for job scripts and namelist files used by WRF and jobs to be submitted to clusters, you should not edit these files.
  * vtables: WRF Vtable files for various model data sources, CFSv2 tables are included in this package.

In this (main) directory, you will find:
  * run_wrf.py: The primary run process which runs Application.py in the background so execution via PuTTy can continue even after a session is disconnected
  * control.txt: A newline terminated text file that sets various parameters on the script (See below section on control.txt)
  * README.md: You're reading it!
  
Additionally, you will need to define a directory inside the repository directory called run_files. The only thing that needs to go in this directory is any geo_em files created by geogrid if you are planning on using a "fixed domain". If you plan on changing domains often, this step is not required.
  
### Control.txt ###
control.txt is a newline terminated text file which contains important parameters needed to run this script. The control.txt file MUST be located in the same directory as the run_wrf.py script file in order for the script to run. The format of this file is simple:

Each command line is split into two breaks:

**variable value**

EX: myvar 12

Would store the value of 12 in a parameter named myvar for the file. Any line that begins with a pound sign (#) is treated as a comment line. These variables are all defined in the AppSettings() class, but for simplicity, here is a list of the parameters accepted by control.txt

These first parameters define program specific settings and define your WRF directories. For help installing the WRF model, please see the included TXT file on installation:
  * debugmode: Setting this variable to 1 will not run any commands, but instead print the commands to the console for debugging / testing purposes. Typically, leave this as 0.
  * need_copy_exe: Set this to 1 if you do not use $PATH to point to your WRF executables, otherwise set this to 0 and set wrfexecutables and wpsdirectory.
  * jobscheduler: Which job scheduler your system is using, see the below section on **job schedulers** for details on adding more. (Currently available are COBALT, SLURM, and PBS)
  * accountname: Your account/project name on your HPC system.
  * sourcefile: For systems that do not use the .bashrc file, you may define a file path that contains your relevant EXPORT and module calls here
  * geogdir: The path to your WPS geography files stored on your machine
  * constantsdir: The path to your dataset constants files
  * datadir: The path to where you want GRIB data to be stored, the full path is: datadir/model source/YYYYMMDDHH/
  * wrfdir: The path to where you want model runs to occur on your machine
  * wrfexecutables: The path to where the WRF executables are located (/main/ folder inside the WRF folder)
  * wrfrunfiles: The path to the WRF's /run/ directory
  * wpsdirectory: The path to your WPS (WRF Preprocessing System) directory
  * tabledir: If you have saved the WPS table files (e.g., GEOGRID.TBL) to a different location that is not in wpsdirectory/geogrid, wpsdirectory/metgrid, set this to point to where the tables are.
  * uppexecutables: The path the the unipost executables (Not required if not using Unipost)
  * postdir: The path to the /post/ directory in this package
  * condamodule: Which anaconda module you would like to load for post processing (Only used if you are using the python post-processing solution, see notes below)

These next parameters define which WRF steps to run, and define some basic WRF parameters to use:
  * starttime: The initialization time for the first forecast hour, the format is YYYYMMDDHH
  * rundays: The number of days to run the model after initialization
  * runhours: The number of hours to run in addition to rundays (IE: total = 24*rundays + runhours)
  * modeldata: The data source used in this run (*See the section below on adding model sources if you want to use something other than CFSv2 or NARR*)
  * run_prerunsteps: A 1/0 flag used to designate if the pre-run steps, including symlinks and directory creations are needed. **Typically, you should leave this as 1 unless debugging errors**
  * run_geogrid: A 1/0 flag used to designate if the geogrid process needs to be run, if you are using the same grid space, run geogrid once and copy the resulting geo_em file to the run_files/ folder, then set the parameter to 0, otherwise geogrid will run.
  * run_preprocessing_jobs: A 1/0 flag used to designate if WPS preprocessing needs to be run (This includes ungrib, metgrid, and real)
  * run_wrf: A 1/0 flag used to designate if the WRF process needs to be run, only turn off if you are debugging a latter step
  * run_postprocessing: This 1/0 flag enables post-processing after the WRF run is completed. At the moment we only support unipost, however a flag for python is included if you would like to make some edits to Jobs.py  
  * post_run_unipost: Set this flag to 1 if you wish to use UPP to post-process
  * post_run_python: Set this flag to 1 if you wish to use Python to post-process

Also defined in control.txt is support for some of the WRF namelist options, the current supported namelist options are as follows:
  * use_io_vars: If you would like to use the IO_VARS WRF option (See the section titled IO_VARS below)
  * wrf_debug_level: The debug level of the WRF model (Default 0, set to powers of 10 for increasing debug output in your WRF logs)
  * e_we: The number of grid spaces in the X direction
  * e_sn: The number of grid spaces in the Y direction
  * e_vert: The number of grid spaces in the Z (Vertical) direction
  * geog_data_res: The text string control for the geographic data resolution (See WPS Geography)
  * dx_y: The set grid spacing. For this program, we set both x & y to equal grid spaces.
  * map_proj: The map projection to use for WRF (By default this is Lambert Conformal Conic)
  * ref_lat: The map reference latitude
  * ref_lon: The map reference longitude
  * truelat1: The "true latitude 1" parameter used by map projections
  * truelat2: The "true latitude 2" parameter used by map projections
  * stand_lon: The "standard longitude" parameter used by map projections
  * p_top_requested: The defined "top" of the atmosphere (In pascals) to use in the model (This will be the highest vertical level)
  * num_metgrid_levels: The number of vertical levels to use for the metgrid process (Dependent on your input data)
  * num_metgrid_soil_levels: The number of soil levels to use for the metgrid process (Dependent on both the input data, and selected microphysics schemes)
  * mp_physics: Which microphysics scheme you would like to use in the model (See: https://esrl.noaa.gov/gsd/wrfportal/namelist_input_options.html)
  * ra_lw_physics: Which longwave radiation physics scheme you would like to use in the model
  * ra_sw_physics: Which shortwave radation physics scheme you would like to use in the model
  * radt: The number of minutes in your model run between radiation physics calls
  * sf_sfclay_physics: Surface layer clay physics option
  * sf_surface_physics: Land-surface option (Dependent on num_soil_layers)
  * bl_pbl_physics: Boundary layer physics option
  * bldt: The number of minutes in your model run between boundary layer physics calls (Set to 0 to run at each step)
  * cu_physics: Convective parameterization scheme (Note: If you are at or below a convective resolving horizontal resolution (dx_y ~ 4KM), set this to 0)
  * cudt: The number of minutes in your model run between convective parameterization calls.
  * num_soil_layers: Number of soil layers in the land surface model (Dependent on sf_surface_physics)
  * num_land_cat: The number of land categories in the input surface data (Dependent on geog_data_res)
  * sf_urban_physics: Urban physics scheme to set in the model
  * hail_opt: Hail switch for WDM6 and Morrison schemes
  * prec_acc_dt: How many minutes between accumulated precipitation calls in your outputs
  
The following parameters in the control file define job specific settings that should be altered based on the system you are running on and performance testing of WRF:
  * num_geogrid_nodes: The number of CPU nodes to use in the geogrid process
  * geogrid_mpi_ranks_per_node: The number of MPI ranks to assign per geogrid node (This is the number of processors per node)
  * geogrid_walltime: The maximum wall time to be required by the geogrid process defined in minutes
  * num_prerun_nodes: The number of CPU nodes to use for the prerun job (ungrib / metgrid / real)
  * prerun_mpi_ranks_per_node: The number of MPI ranks to assign per node for the prerun job (NOTE: If you are using parallel IO this should be identical to geogrid_mpi_ranks_per_node)
  * prerun_walltime: The maximum wall time to be required by the prerun job (In minutes)
  * num_wrf_nodes: The number of nodes to run for the WRF job
  * wrf_walltime: The maximum wall time to be required by the WRF job (In minutes)
  * wrf_mpi_ranks_per_node: The number of MPI ranks to assign per node for the WRF job (This is also PPN)
  * wrf_numtiles: The numtiles parameter for WRF, this is for patch based processing and may aid with performance times in some cases, use multiples of 2
  * wrf_nio_tasks_per_group: The number of MPI rasks to direct to file I/O (NOTE: ONLY USE THIS IF YOUR SYSTEM SUPPORTS QUILTING FILES, IE: LUSTRE FILE SYSTEM)
  * wrf_nio_groups: The number of nodes in the WRF job to direct to file I/O (NOTE: ONLY USE THIS IF YOUR SYSTEM SUPPORTS QUILTING FILES)
  * lfs_stripe_count: The stripe count to assign to WRF output files, used for quilting to improve I/O on supported systems (Set to 0 to disable this in the program).
  * wrf_detect_proc_count: A 1/0 flag which identifies if the program should assign nproc_x and nproc_y based on Balle and Johnsen, 2016 findings

The last batch on control parameters are for post-processing options:
  * unipost_out: The file type to generate from unipost (GRIB or GRIB2)
  * num_upp_nodes: The number of CPU nodes to use in your unipost job
  * upp_ensemble_nodes_per_hour: How many nodes should be split from the total node count for each output file (Should be divisible by num_upp_nodes)
  * upp_walltime: The maximum wall time to be required by your unipost job (In minutes)
  * num_python_nodes: The number of CPU nodes to use in your python job
  * python_threads_per_rank: The number of MPI ranks to assign per python node (PPN)
  * python_walltime: The maximum wall time to be required by your python job (In minutes)  
  
If you would like to add more options, you will need to do three things:

  1. Create a new "key" in ApplicationSettings.py for the namelist option you would like to include
  2. Edit the namelist.input.template file to replace the default setting with the defined key, e.g. [e_we]
  3. Add your new key and default value to control.txt
  
### How to use this program ###
Start by completing the installation of the WRF model and the WPS programs on your cluster. Once completed, edit the control.txt file to point to the correct directories (These variables in control.txt are **wrfexecutables**, **wrfrunfiles**, and **wpsexecutables**). Then, you need to define the directory parameters (geogdir, tabledir, and wrfdir). By default, this script package is equipped to run WRF using CFSv2 (NARR Support is also included, but must be set in control.txt) data, however you may add other sources if you please (See the section below titled Adding Model Sources).

The run time parameters (starttime, rundays, runhours) need to be defined in the control.txt file, remember that runhours is in ADDITION to rundays, so keep that in mind when setting these parameters. It is recommended to run multiple "test jobs" using different node/processor count settings to find the ideal times on your HPC system, there are numerous papers in the body of literature you may investigate to get an idea on good starting points. Once your control.txt file has been written you may run the python script **run_wrf.py** from the head directory to push the process to the background (Allowing you to safely close an SSH session and let the process completely run), or, if you want the output pushed to your SSH client, you may run **Application.py** in the scripts/ directory (Please note this script will not run in the background, so if you are disconnected, the script will terminate at the position it is at). All logging information will be saved to a log file in the scripts/ directory, and will be moved to a /logs/ folder upon script completion.
  
### Adding Model Sources ###
This script package was written for the Climate Forecast System version 2.0 (CFSv2) forecast system or the North American Regional Reanalysis (NARR) as input for the WRF model, however the script package is dynamic enough to allow for quick additions of other model sources.

First, you will need to obtain the VTable files for your specific model data source and include these in the vtables directory in this package.

Second, you'll need to add some basic model information to the *ModelDataParameters* class instance, located near the top of the scripts/ModelData.py file. A dictionary is contained in this class with the following format:
```python
			"CFSv2": {
				"VTable": ["Vtable.CFSv2.3D", "Vtable.CFSv2.FLX"],
				"FileExtentions": ["3D", "FLX"],
				"FGExt": "\'3D\', \'FLX\'",
				"HourDelta": 6,
				"ConstantsFile": "constant_file",
				"CanDownloadDirectly": True,				
			},
```
The name of the dictionary instance should ideally be the model data source. *VTable* is a list instance containing all VTable files contained in the head folder used by this model data source. *FileExtentions* is a list of all file extensions used by the incoming GRIB data, for specific models (IE: CFSv2), multiple files are needed, hence this allows it. *FGExt* is a parameter applied by namelist.wps for the extensions of the ungribbed files used by the metgrid process, make this similar to the GRIB files. *HourDelta* is the amount of hours separating each incoming GRIB file. *ConstantsFile* is a point to the associated WRF constants file for the specific dataset (See NARR Constants File for more info). Lastly, *CanDownloadDirectly* is a boolean flag to specify if the script package will be able to fetch the file through simple 'wget' calls, or False if the data will be collected manually.

Next, scroll down to the *ModelData* class and find the pooled_download section. You will need to incorporate an additional if/elif clause for your new model that downloads the model data if it can auto-download the files, here is a sample:

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

If your data source does not support auto downloads, the script will check upon running to ensure the needed files are present and abort with an error message if they are not, or in the wrong location. Finally to activate a data set, change the modeldata parameter in control.txt to match your model source.

I highly recommend that if you are successful in getting a new data source to be compatable with this script package to **send in a pull request** containing your updated ModelData.py file such that others can take advantage of your findings!

### Job Schedulers ###
This script package is designed to be used on high-performance computing environments (HPC) that employ resource management tools to allocate work across nodes. In order to use these systems you must have an account / project allocation on the system and have a basic understanding of how to submit jobs on these systems ([Here is an example page](https://www.lcrc.anl.gov/for-users/using-lcrc/running-jobs/running-jobs-on-bebop/) from Argonne's LCRC System).

At the moment, this package can submit jobs to the COBALT and SLURM job schedulers (Fully tested) and the PBS scheduler (Needs testing). The definitions for the schedulers are defined in Scheduler.py and controlled by the **jobscheduler** option in control.txt. If you would like to add support for another job scheduling system you will need to edit Scheduler.py to add your scheduler and the respective options. Here is an example block from the SLURM scheduler:

```python
			"SLURM": {
				"header-type": "#!/bin/bash",
				"header-tag": "#SBATCH",
				"header-jobname": "--job-name",
				"header-account": "--account",
				"header-nodes": "--nodes",
				"header-tasks": "--ntasks-per-node",
				"header-jobtime": "--time",
				"header-jobqueue": None,
				"extra-exports": None,
				"cmdline": "",
				"time-format": "timestring",
				"subcmd": "sbatch",
				"runcmd": "srun",
				"subargs": "-n [total_processors]"
			},	
```

Here's what each of these dictionary entries control:
  * header-type: This defined what type of file you are in, as far as I'm aware, most if not all of these should be BASH files and use *#!/bin/bash*
  * header-tag: Each job scheduler has a list of definition lines at the top of the file that begins with a tag (IE: #COBALT blah=value), this defines that tag
  * header-jobname: If your scheduler supports naming a job, this defines the variable name for the job name, use **None** here if it does not.
  * header-account: This defined the account/project statement, unless you are running your own cluster this should be defined on each. If not needed, use **None**.
  * header-nodes: This definition specifies the node argument
  * header-tasks: This definition specifies the tasks per node (Also called processors or PPN) argument
  * header-jobtime: This specifies the argument for the wall clock argument.
  * header-jobqueue: If your cluster requires usage of different queues, this is where you define that parameter.
  * extra-exports: This is a specialized line that tells the script it needs to add a batch of lines below the header for export statements, see the COBALT example in Application.py for more details.
  * cmdline: This controls any additional command line arguments required after job submission commands for your scheduler.
  * time-format: This is either minutes (Single integer) or timestring (HH:MM:SS). If your scheduler needs something else, please get in touch with me and I'll show you how to get your method installed.
  * subcmd: This is the job submission command (What is called from the command line to push your job to the queue)
  * runcmd: This is the command inside your jobscript to start your executable
  * subargs: This is additional arguments sent to the runcmd. [total_processors] is a template that is nodes * PPN. You may add others as needed, see Application.py for more info.

### IO_VARS ###
This script package has limited support for post-processing using the IO_VARS file option in WRF (iofields_filename namelist option). This namelist option allows your wrfout files to be significantly truncated to only contain pertinant output fields to significantly cut down on both file I/O times and compute times in your model.

An example line of IO_VARS.txt follows:

+:h:5:REFD_COM

The format of each line is as such:

  * +: This says to "add" the following to the respective file, using '-' would be a remove call
  * h: This says the target is a history output stream (wrfout, auxhistory, etc)
  * 5: This is the target stream for the history file (This would be auxhistory5)
  * REFD_COM: This is the target field to be added/removed.
  
You can combine multiple fields in a single line as well:

-:h:5:XLAT,XLONG,HGT,LANDMASK

This would remove XLAT, XLONG, HGT, and LANDMASK from the auxhistory5 output.

### Python Post-Processing ###
This package contains a basic python post-processing script that incorporates multiple other python packages. If you would like to use the python post-processor you first need to set **post_run_python** to 1 in **control.txt**. This will create a job-script to execute PythonPost.py in parallel using Dask and wrf-python. Controlling the outputs of this are handled by a second control text file located in the Python/ directory.

Here are the available fields that may be visualized:

  * Temperature
  * Pressure (MSLP)
  * Winds
  * Simulated Reflectivity
  * Precipitation Type [IN DEVELOPMENT]
  * Accumulated Precipitation
  * Accumulated Snowfall
  * Precipitable Water
  * Dewpoint Temperature
  * Omega
  * 10m Max Wind Gusts
  * Theta-E (Equiv. Pot. Temp)
  * Geopotential Height
  * Relative Humidity
  * 500mb Relative Vorticity
  * 3D CAPE
  * 3D CIN
  * MUCAPE
  * MUCIN
  * Lifting Condensation Level
  * Level of Free Convection
  * Wind Shear
  * Storm Relative Helicity
  * Updraft Helicity
  * AFWA Parameters
  
To control the fields that are output, you need to edit the **python_post_control.txt** file located in the /Post/Python/ directory. This has a similar format to the base control.txt file with the addition of array-like element support. Here is a list of the parameters for this file:

This first batch of configuration options are used for internal processing and do not control plotting:
  * save_datafiles_when_done: A 1/0 flag to save the resulting netCDF4 file after plotting is done, or delete them.
  * create_animated_gifs: A 1/0 flag to instruct the program to generate animated .GIF files using all timesteps of the image.
  * gif_timestep: How many frames per second (FPS) will be used for makign the GIF images
  * sftp_push_results_when_done: A 1/0 flag to SFTP the resulting files from this machine when done
  * sftp_push_saved_datafile: A 1/0 flag to SFTP the resulting netCDF4 datafiles when done, only active if save_datafiles_when_done is also on.
  * sftp_server: The web link or IP address of the target server
  * sftp_server_port: Which port to use for SFTP (Defaults to 22)
  * sftp_user: The username to log in with
  * sftp_pass: The passwork to use to log in
  
This second batch of options is used to define what plotting is done:
  * plot_surface_map: A flag to plot a surface map (See next three options)
  * plot_surface_map_temperature: A flag used to toggle filled temperature contours on the surface map
  * plot_surface_map_winds: A flag used to toggle wind barbs on the surface map
  * plot_surface_map_mslp: A flag used to toggle contour lines of mean sea level pressure on the surface map
  * plot_simulated_reflectivity: A flag to plot a map of simulated radar reflectivity
  * plot_precip_type: A flag used to plot a map of precipitation type [IN DEVELOPMENT]
  * plot_accumulated_precip: A flag used to plot a map of total accumulated precipitation
  * plot_accumulated_snowfall: A flag used to plot a map of total accumulated snowfall
  * plot_precipitable_water: A flag used to plot a map of precipitable water
  * plot_precipitable_water_with_mslp_contours: A flag used to instruct the plotter to add MSLP contours to the precipitable water plot (Only active if the above is on).
  * plot_dewpoint_temperature: A flag used to plot a map of surface dewpoint temperature
  * plot_surface_omega: A flag used to plot a map of surface omega
  * plot_10m_max_winds: A flag used to plot a map of the maximum 10m wind gusts
  * plot_upper_lv_winds: A flag used to plot a map of upper-level winds
  * plot_upper_lv_winds_withheights: A flag used to instruct the plotter to add geopotential height contours to the upper level wind map
  * upper_winds_levels: An array-like field to instruct which levels to plot the upper-level winds on (See below for more info)
  * plot_theta_e: A flag used to plot a map of equivalent potential temperature
  * plot_theta_e_heights: A flag used to instruct the plotter to add geopotential height contours to the theta-e map
  * plot_theta_e_winds: A flag used to instruct the plotter to add wind barbs to the theta-e map
  * theta_e_levels: An array-like field to instruct which levels to plot theta-e on (See below for more info)
  * plot_rh_and_wind: A flag used to plot a map of relative humidity and winds
  * rh_and_wind_levels: An array-like field to instruct which levels to plot RH and winds on (See below for more info)
  * plot_500_rel_vort: A flag used to plot a map of 500mb relative vorticity
  * plot_500_rel_vort_withheights: A flag used to instruct the plotter to add geopotential height contours to the relative vorticity map
  * plot_CAPE: A flag used to plot a map of surface based convective available potential energy
  * plot_CIN: A flag used to plot a map of surface based convective inhibition
  * plot_MUCAPE: A flag used to plot a map of most unstable CAPE (MUCAPE)
  * plot_MUCIN: A flag used to plot a map of most unstable CIN (MUCIN)
  * plot_LCL: A flag used to plot a map of the lifting condenstion level
  * plot_LFC: A flag used to plot a map of the level of free convection
  * plot_AFWA_Hail: A flag used to plot a map of the AFWA Hail Diagnostic
  * plot_AFWA_Tor: A flag used to plot a map of the AFWA Tornado Diagnostic
  * plot_shear: A flag used to plot a map of wind shear from the surface to a defined upper bound (Next parameter)
  * shear_levels: An array-like field that defines the upper bounds of wind shear to use
  * plot_srh: A flag used to plot a map of the storm relative helicity from the surface to defined upper bounds (Next parameter)
  * srh_levels: An array-like field that defines the upper bounds of SRH to use
  * plot_updft_helcy: A flag used to plot a map of updraft helicity between levels
  * updft_helcy_levels: An array-like field that defines the levels of updraft helicity to plot, NOTE: You may define multiple layers to use here, but the number of values must be divisible by 2.
  
Some of the above field have support for "array-like" options. This means it will be loaded into the system as a list and then parsed at each of the defined parameters. Here is an example of one of these parameters:

upper_winds_levels (int)[925,850,700,500,300,250,200]

The formatting starts with a singular argument in parenthesis to define the datatype transformation (How python will treat the value). If you do not define this, it will be loaded as a string. There is support for integer (int) and float (float) transformations. Next, enclose in square brackets the values you want to use. **NOTE:** You cannot include spaces between these values, ie:
upper_winds_levels (int)[925, 850, 700, 500, 300, 250, 200]
Would be wrong.

Most of the standard paramters use this as interpolation to a pressure level, you may include the surface as well by having the first element of the array be a 0.

ie:

upper_winds_levels (int)[0,925,850,700,500,300,250,200]
				
Would save the U & V components of the wind at the surface, 925mb, 850mb, 700mb, 500mb, 300mb, 250mb, and 200mb.				
				
### Contact Info ###
Any questions regarding the script package can be sent to Robert C. Fritzen (rfritzen1@niu.edu). In-person questions can be done from my office in Davis Hall, room 209.