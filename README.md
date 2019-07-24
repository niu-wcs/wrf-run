# WRF on Theta @ Argonne #
## Dpt. Geographic & Atmospheric Sciences ##
## By: Robert C. Fritzen ##

### Introduction ###
This python script package automates the entire WRF process for use on cluster based computers (This package automates for Argonne's Theta Cluster). This is a fully self-contained script package that handles the tasks of obtaining the data, running the pre-processing executables, the WRF process, and forking the task to post-processing scripts for visualization.

### Requirements ###
Included in this repository is a post-processing solution written in Python 3 as well as a UPP wrapper. If you want to use UPP, you may ignore this section, however, if you plan on using the Python module, you will need three other Python Packages to be installed:
  * wrf-python: https://github.com/NCAR/wrf-python
  * dask: https://github.com/dask/dask
  * dask-jobqueue: https://github.com/Phantom139/dask-jobqueue (This is a custom fork that has support for Argonne's Theta Machine)

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
	* Logging: Singleton class instance that handles logging the program process to a text file
	* ModelData.py: Classes and methods used to manage various data sources for the model
	* PreparePyJob.py: Class instance used to construct and monitor the Python Post-Processing job
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
  
Additionally, you will need to define a directory inside the repository directory called run_files. The only thing that need to go in this directory is any geo_em files created by geogrid if you are planning on using a "fixed domain". If you plan on changing domains often, this step is not required.
  
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
  * wrfexecutables: The path to where the WRF executables are located (/main/ folder inside the WRF folder)
  * wrfrunfiles: The path to the WRF's /run/ directory
  * wpsexecutables: The path to where the WRF WPS executables are located (Top directory of the /WPS/ folder)
  * uppexecutables: The path the the unipost executables (Not required if not using Unipost)
  * modeldata: The data source used in this run (*See the section below on adding model sources if you want to use something other than CFSv2*)
  * run_prerunsteps: A 1/0 flag used to designate if the pre-run steps, including symlinks and directory creations are needed. **Typically, you should leave this as 1 unless debugging errors**
  * run_geogrid: A 1/0 flag used to designate if the geogrid process needs to be run, if you are using the same grid space, run geogrid once and copy the resulting geo_em file to the run_files/ folder, then set the parameter to 0, otherwise geogrid will run.
  * run_ungrib: A 1/0 flag used to designate if the ungrib process needs to be run, only turn off if you are debugging a latter step
  * run_metgrid: A 1/0 flag used to designate if the metgrid process needs to be run, only turn off if you are debugging a latter step
  * run_real: A 1/0 flag used to designate if the real process needs to be run, only turn off if you are debugging a latter step
  * run_wrf: A 1/0 flag used to designate if the WRF process needs to be run, only turn off if you are debugging a latter step
  * run_postprocessing: This 1/0 flag enables post-processing after the WRF run is completed. At the moment we only support unipost, however a flag for python is included if you would like to make some edits to Jobs.py  
  * mpi_ranks_per_node: The number of MPI ranks (Processors) to run for each task, by default this is set to 32.
  * num_geogrid_nodes: The number of CPU nodes to use in the geogrid process
  * geogrid_walltime: The maximum wall time to be required by the geogrid process
  * num_prerun_nodes: The number of nodes to run for the prerun job (Ungrib, Metgrid, and Real)
  * num_metgrid_processors: The number of CPU processors to use specifically for metgrid
  * num_real_processors: The number of CPU processors to use specifically for the real.exe process
  * prerun_walltime: The maximum wall time to be required by the prerun job (Remember this accounts for Ungrib, Metgrid, and Real, please set accordingly)
  * num_wrf_nodes: The number of CPU nodes to use in the WRF process
  * wrf_walltime: The maximum wall time to be required by the WRF process  
  * post_run_unipost: Set this flag to 1 if you wish to use UPP to post-process
  * post_run_python: Set this flag to 1 if you wish to use Python to post-process
  * unipost_out: A textual flag to indicate whether UPP should export to GRIB or GRIB2, the two choices are grib and grib2
  * num_upp_nodes: The number of CPU nodes to use in the UPP process
  * upp_ensemble_nodes_per_hour: UPP is broken into an ensemble job, this is the number of nodes from the num_upp_nodes to allocate to each individial task at any given time
  * upp_walltime: The maximum wall time to be required by the UPP process
  
Additionally, inside the control.txt is support for some of the WRF namelist options, the current supported namelist options are as follows:

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
  * nio_tasks_per_group: WRF Namelist option, the number of MPI tasks to direct to file I/O
  * nio_groups: WRF Namelist option, the number of nodes to direct to file I/O  
  
If you would like to add more options, you will need to do three things:

  1. Create a new "key" in ApplicationSettings.py for the namelist option you would like to include
  2. Edit the namelist.input.template file to replace the default setting with the defined key, e.g. [e_we]
  3. Add your new key and default value to control.txt
  
### How to use this program ###
Start by completing the installation of the WRF model and the WPS programs on your cluster. Once completed, edit the control.txt file to point to the correct directories (These variables in control.txt are **wrfexecutables**, **wrfrunfiles**, and **wpsexecutables**). Then, you need to define the directory parameters (geogdir, tabledir, and wrfdir). By default, this script package is equipped to run WRF using CFSv2 data, however you may add other sources if you please (See the section below titled Adding Model Sources).

The run time parameters (starttime, rundays, runhours) need to be defined in the control.txt file, remember that runhours is in ADDITION to rundays, so keep that in mind when setting these parameters. You may adjust the nodes and processors settings as necessary, however these have been provided default values based on multiple tests such that you shouldn't have to. Once your control.txt file has been written you may run the python script **run_wrf.py** from the head directory to push the process to the background (Allowing you to safely close an SSH session and let the process completely run), or, if you want the output pushed to your SSH client, you may run **Application.py** in the scripts/ directory (Please note this script will not run in the background, so if you are disconnected, the script will terminate at the position it is at). All logging information will be saved to a log file in the scripts/ directory, and will be moved to a /logs/ folder upon script completion.
  
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