#!/usr/bin/python
# PythonPost.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This is the main python file called by the post-processing job and handles the parallel
#  processing on the wrfout files.

import os
import sys
import glob
import time
#from ..scripts import Tools
import PyPostTools
import Calculation
import ArrayTools
import PyPostSettings
import Routines
import Plotting
import xarray
import dask.array as da
from dask.array import map_blocks
from dask.distributed import Scheduler, Client, progress, metrics, wait
from datetime import datetime
import tornado.util
from tornado.ioloop import IOLoop
from threading import Thread
import socket

"""
RF: Debug Mode Calls for Dask (Disable on release)
"""
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

dask_client = None
dask_nodes = 0
dask_threads = 0
scheduler_port = 12345

def launch_python_post():
	curDir = os.path.dirname(os.path.abspath(__file__)) 
	logger = PyPostTools.pyPostLogger()

	logger.write("Initializing WRF Python Post-Processing Program")
	#Step 1: Load program settings
	logger.write(" 1. Application Initalization")
	logger.write("  - Loading control file, python_post_control.txt")
	_pySet = PyPostSettings.PyPostSettings()
	logger.write("  - Success!")
	logger.write("  - Testing Environmental Variables")
	try:
		dask_nodes = os.environ["PYTHON_POST_NODES"]
		dask_threads = os.environ["PYTHON_POST_THREADS"]	
		postDir = os.environ["PYTHON_POST_DIR"]
		targetDir = os.environ["PYTHON_POST_TARG_DIR"]
	except KeyError:
		logger.write("***FAIL*** KeyError encountered while trying to access important environmental variables, abort.")
		sys.exit("")
	logger.write("  - Success!")
	logger.write("  - Initializing Dask (" + str(dask_nodes) + " Nodes Requested), Collecting routines needed")
	_routines = Routines.Routines()
	# Start Dask Tasks
	cLoop = IOLoop.current()
	t = Thread(target = cLoop.start, daemon = True)
	t.start()
	logger.write("   - Tornado IO Loop initialized...")
	s = Scheduler(loop = cLoop, dashboard_address = None)
	s.start("tcp://: " + str(scheduler_port))
	logger.write("   - Dask Scheduler initialized (Port " + str(scheduler_port) + ")...")
	dask_client = Client("tcp://" + socket.gethostname() + ":" + str(scheduler_port))
	logger.write("   - Dask Client initialized...")
	logger.write("   - Writing Dask Worker Job Files...")
	with PyPostTools.cd(targetDir):
		writeFile1 = PyPostTools.write_job_file(socket.gethostname(), scheduler_port, project_name="climate_severe", queue="debug-cache-quad", nodes=dask_nodes, wall_time=60, nProcs=1)
		writeFile2 = PyPostTools.write_worker_file(socket.gethostname(), scheduler_port, nProcs=1)
		if(writeFile1 == False or writeFile2 == False):
			dask_client.close()
			logger.write("   - Failed to write job files, are you missing an important parameter?")
			sys.exit("")
			return
		else:
			logger.write("   - Dask Worker Job File Written, Submitting to Queue.")
			PyPostTools.popen("chmod +x launch-worker.sh")
			PyPostTools.popen("chmod +x dask-worker.job")
			PyPostTools.popen("qsub dask-worker.job")
	# Wait here for workers.
	logger.write("   -> Worker Job submitted to queue, waiting for workers...")
	while len(dask_client.scheduler_info()['workers']) < int(dask_nodes):
		time.sleep(2)
	logger.write("   -> Workers are now connected.")
	#logger.write("   - Adding local packages to dask workers")
	#dask_client.upload_file("PyPostTools.py")
	#dask_client.upload_file("ArrayTools.py")
	#dask_client.upload_file("Calculation.py")
	#dask_client.upload_file("ColorMaps.py")
	#dask_client.upload_file("Conversions.py")
	#dask_client.upload_file("Plotting.py")
	#dask_client.upload_file("PyPostSettings.py")
	#dask_client.upload_file("Routines.py")	
	logger.write("  - Success!")
	logger.write(" 1. Done.")
	logger.write(" 2. Start Post-Processing Calculations")
	calculation_future = start_calculations(dask_client, _routines, dask_threads)
	if(calculation_future != None):
		wait(calculation_future)
		result_calc = dask_client.gather(calculation_future)[0]
		if(result_calc != 0):
			logger.write("***FAIL*** An error occured in calculations method, check worker logs for more info.")
			logger.close()
			sys.exit("")
	logger.write(" 2. Done.")
	logger.write(" 3. Generating Figures")
	logger.write("  - Collecting files from target directory (" + targetDir + ").")
	fList3 = sorted(glob.glob(targetDir + "WRFPRS_F*"))
	logger.write("  - " + str(len(fList3)) + " files have been found.")
	logger.write(" -> Pushing run_plotting_routines() to dask.")
	fullDict = _pySet.get_full_dict()
	plotting_future = start_plotting(dask_client, fullDict, dask_threads)
	wait(plotting_future)
	result_plot = dask_client.gather(plotting_future)[0]
	if(result_plot != 0):
		logger.write("***FAIL*** An error occured in plotting method, check worker logs for more info.")
		logger.close()
		sys.exit("")	
	logger.write(" 3. Done.")
	logger.write(" 4. Final Steps")
	
	logger.write(" 4. Done, Closing Dask Client.")
	dask_client.retire_workers(workers=dask_client.scheduler_info()['workers'], close=True)
	dask_client.close()	
	logger.write("All Steps Completed.")
	logger.write("***SUCCESS*** Program execution complete.")
	logger.close()

def start_calculations(dask_client, _routines, dask_threads):	
	logger = PyPostTools.pyPostLogger()
	try:
		start = os.environ["PYTHON_POST_FIRSTTIME"]
		postDir = os.environ["PYTHON_POST_DIR"]
		targetDir = os.environ["PYTHON_POST_TARG_DIR"]
	except KeyError:
		logger.write("***FAIL*** Could not locate environment variables set by the original application (DIRS), check the logs to ensure it is being done.")
		logger.close()
		sys.exit("Failed to find environmental variable (DIRS), check original application to ensure it is being set.")		
		return -1
	# Get the list of files
	logger.write("  - Collecting files from target directory (" + postDir + ").")
	fList = sorted(glob.glob(postDir + "wrfout*"))
	logger.write("  - " + str(len(fList)) + " files have been found.")
	logger.write("  - Checking target directory if this job has been done?")
	fList2 = sorted(glob.glob(targetDir + "WRFPRS_F*"))
	if(len(fList) == len(fList2)):
		logger.write("   - " + str(len(fList2)) + " WRFPRS files have been found, calculations are already completed, skipping step.")
		return None
	logger.write("   - No.")
	logger.write("Pushing run_calculation_routines() to dask.")
	
	call_list = [{'filename' : fitem, 'start': start, 'tDir': targetDir, 'routines' : _routines, 'dask_threads': dask_threads} for fitem in fList]
	
	calculation_future = dask_client.map(run_calculation_routines, call_list)
	return calculation_future
	
def start_plotting(dask_client, fullDict, dask_threads):	
	logger = PyPostTools.pyPostLogger()
	try:
		targetDir = os.environ["PYTHON_POST_TARG_DIR"]
	except KeyError:
		logger.write("***FAIL*** Could not locate environment variables set by the original application (DIRS), check the logs to ensure it is being done.")
		logger.close()
		sys.exit("Failed to find environmental variable (DIRS), check original application to ensure it is being set.")		
		return -1
	# Get the list of files
	logger.write("  - Collecting files from target directory (" + targetDir + ").")
	fList = sorted(glob.glob(targetDir + "WRFPRS_F*"))
	logger.write("  - " + str(len(fList)) + " files have been found.")
	logger.write("Pushing run_plotting_routines() to dask.")
	
	call_list = [{'filename' : fitem, 'tDir': targetDir, 'settings' : fullDict, 'dask_threads': dask_threads} for fitem in fList]
	
	plotting_future = dask_client.map(run_plotting_routines, call_list)
	return plotting_future	
	
def run_calculation_routines(callObject):
	import ArrayTools
	import Calculation
	import Routines
	import PyPostTools

	ncFile_Name = callObject['filename']
	start = callObject['start']
	targetDir = callObject['tDir']
	_routines = callObject['routines']
	dask_threads = callObject['dask_threads']
	logger = PyPostTools.pyPostLogger()
	
	if(start == "" or targetDir == ""):
		logger.write("Cannot run calculations, missing important information")
		return -1
	
	startTime = datetime.strptime(start, '%Y%m%d%H')
	daskArray = xarray.open_mfdataset(ncFile_Name, parallel=True)
	forecastTime_str = ncFile_Name[-19:]
	forecastTime = datetime.strptime(forecastTime_str, '%Y-%m-%d_%H_%M_%S')
	elapsedTime = forecastTime - startTime
	elapsedHours = elapsedTime.days*24 + elapsedTime.seconds//3600
	# Grab the vertical interpolation levels
	p_vert = Calculation.get_full_p(daskArray)
	z_vert = Calculation.get_height(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
	# Our end goal is to create a new xArray saving only what we need to it. Start by creaying a "blank" xarray
	xrOut = xarray.Dataset()
	# Start with important attributes
	xrOut.attrs["MOAD_CEN_LAT"] = daskArray.MOAD_CEN_LAT
	xrOut.attrs["CEN_LON"] = daskArray.CEN_LON
	xrOut.attrs["TRUELAT1"] = daskArray.TRUELAT1
	xrOut.attrs["TRUELAT2"] = daskArray.TRUELAT2
	xrOut.attrs["MAP_PROJ"] = daskArray.MAP_PROJ
	xrOut.attrs["DX"] = daskArray.DX
	xrOut.attrs["DY"] = daskArray.DY
	xrOut.attrs["STARTTIME"] = start
	xrOut.attrs["FORECASTHOUR"] = elapsedHours	
	# Copy map information first
	xrOut.coords["XLAT"] = (('south_north', 'west_east'), daskArray["XLAT"][0])
	xrOut.coords["XLONG"] = (('south_north', 'west_east'), daskArray["XLONG"][0])		
	# Now, calculate the variables.
	##
	## - MSLP
	if(_routines.need_mslp):
		print("MSLP - " + str(ncFile_Name))
		mslp = Calculation.get_slp(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["MSLP"] = (('south_north', 'west_east'), mslp)
		del(mslp)
	##
	## - Simulated Radar Reflectivity			
	if(_routines.need_sim_dbz):
		print("SDBZ - " + str(ncFile_Name))
		dbz = Calculation.get_dbz(daskArray, use_varint=False, use_liqskin=False, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["DBZ"] = (('south_north', 'west_east'), dbz[0])
		del(dbz)
	##
	## - Precipitation Type			
	if(_routines.need_ptype):
		# Need to make a routine for this.
		print("***WARNING*** Precipitation type is currently unsupported, ignoring.")
	##
	## - Total Accumulated Precipitation			
	if(_routines.need_acum_pcp):
		print("APCP - " + str(ncFile_Name))
		acum_pcp = Calculation.get_accum_precip(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["ACUM_PCP"] = (('south_north', 'west_east'), acum_pcp)
		del(acum_pcp)
	##
	## - Total Accumulated Snowfall			
	if(_routines.need_acum_sno):
		print("ASNO - " + str(ncFile_Name))
		acum_sno = ArrayTools.fetch_variable(daskArray, "SNOWNC")
		xrOut["ACUM_SNO"] = (('south_north', 'west_east'), acum_sno)
		del(acum_sno)
	##
	## - Precipitable Water			
	if(_routines.need_prec_wat):
		print("PWAT - " + str(ncFile_Name))
		prec_wat = Calculation.get_pw(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["PW"] = (('south_north', 'west_east'), prec_wat)
		del(prec_wat)
	##
	## - Dewpoint Temperature			
	if(_routines.need_dewpoint):
		print("TDPT - " + str(ncFile_Name))
		td = Calculation.get_dewpoint(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["TD"] = (('south_north', 'west_east'), td[0])
		del(td)
	##
	## - Relative Humidity			
	if(_routines.need_RH):
		print("RELH - " + str(ncFile_Name))
		rh = Calculation.get_rh(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		for l in _routines.rh_levels:
			if(l == 0):
				xrOut["SFC_RH"] = (('south_north', 'west_east'), rh[0])
			else:
				rh_level = ArrayTools.wrapped_interplevel(rh, p_vert, l, omp_threads=dask_threads, num_workers=dask_nodes) 
				xrOut["RH_" + str(l)] = (('south_north', 'west_east'), rh_level[0])
				del(rh_level)
		del(rh)		
	##
	## - Air Temperature			
	if(_routines.need_Temp):
		print("AIRT - " + str(ncFile_Name))
		tk = Calculation.get_tk(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		for l in _routines.temp_levels:
			if(l == 0):
				xrOut["SFC_T"] = (('south_north', 'west_east'), tk[0])
			else:
				tk_level = ArrayTools.wrapped_interplevel(tk, p_vert, l, omp_threads=dask_threads, num_workers=dask_nodes) 
				xrOut["T_" + str(l)] = (('south_north', 'west_east'), tk_level[0])
				del(tk_level)
		del(tk)
	##
	## - U/V Wind Components			
	if(_routines.need_winds):
		print("WIND - " + str(ncFile_Name))
		for l in _routines.winds_levels:
			# We can handle the 0 as surface here because this function defaults to surface winds when requested_top == 0
			u, v = Calculation.get_winds_at_level(daskArray, vertical_field=p_vert, requested_top=l)
			if(l == 0):
				xrOut["SFC_U"] = (('south_north', 'west_east'), u)
				xrOut["SFC_V"] = (('south_north', 'west_east'), v)
			else:
				xrOut["U_" + str(l)] = (('south_north', 'west_east'), u[0])
				xrOut["V_" + str(l)] = (('south_north', 'west_east'), v[0])
	##
	## - Equivalent Potential Temperature (Theta_E)					
	if(_routines.need_theta_e):
		print("THTE - " + str(ncFile_Name))
		eth = Calculation.get_eth(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		for l in _routines.theta_e_levels:
			if(l == 0):
				xrOut["SFC_THETA_E"] = (('south_north', 'west_east'), eth[0])
			else:
				eth_level = ArrayTools.wrapped_interplevel(eth, p_vert, l, omp_threads=dask_threads, num_workers=dask_nodes) 
				xrOut["THETA_E_" + str(l)] = (('south_north', 'west_east'), eth_level[0])
				del(eth_level)
		del(eth)
	##
	## - Omega			
	if(_routines.need_omega):
		print("OMGA - " + str(ncFile_Name))
		omega = Calculation.get_omega(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["OMEGA"] = (('south_north', 'west_east'), omega[0])
		del(omega)
	##
	## - Max Surface Wind Gust (AFWA Diagnostic)			
	if(_routines.need_sfc_max_winds):
		print("MWND - " + str(ncFile_Name))
		maxWind = ArrayTools.fetch_variable(daskArray, "WSPD10MAX")
		xrOut["MAX_WIND_SFC"] = (('south_north', 'west_east'), maxWind)
		del(maxWind)
	##
	## - Geopotential Height			
	if(_routines.need_geoht):
		print("GHGT - " + str(ncFile_Name))
		for l in _routines.geoht_levels:
			z_level = ArrayTools.wrapped_interplevel(z_vert, p_vert, l, omp_threads=dask_threads, num_workers=dask_nodes) 
			xrOut["GEOHT_" + str(l)] = (('south_north', 'west_east'), z_level[0])
			del(z_level)	
	##
	## - 500 mb Relative Vorticity			
	if(_routines.need_relvort):
		print("RLVT - " + str(ncFile_Name))
		rvo = Calculation.get_rvor(daskArray, omp_threads=dask_threads, num_workers=dask_nodes) 
		rvo_500 = ArrayTools.wrapped_interplevel(rvo, p_vert, 500, omp_threads=dask_threads, num_workers=dask_nodes) 
		xrOut["RVO_500"] = (('south_north', 'west_east'), rvo_500[0])
		del(rvo)
		del(rvo_500)
	##
	## - Convective Available Potential Energy (3D) & Convective Inhibition (3D)			
	if(_routines.need_3d_cape or _routines.need_3d_cin):
		print("3DCAPE - " + str(ncFile_Name))
		cape3d = Calculation.get_cape3d(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		cape = cape3d[0]
		cin = cape3d[1]
		if(_routines.need_3d_cape):
			xrOut["CAPE_3D"] = (('bottom_top', 'south_north', 'west_east'), cape)
		if(_routines.need_3d_cin):
			xrOut["CIN_3D"] = (('bottom_top', 'south_north', 'west_east'), cin)
		del(cape3d)
		del(cape)
		del(cin)
	##
	## - Maximum Cape (MUCAPE, 2D), Maximum CIN (MUCIN, 2D), Lifting Condensation Level (LCL), Level of Free Convection (LFC)			
	if(_routines.need_mucape or _routines.need_mucin or _routines.need_lcl or _routines.need_lfc):
		print("2DCAPE - " + str(ncFile_Name))
		cape2d = Calculation.get_cape2d(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		mucape = cape2d[0]
		mucin = cape2d[1]
		lcl = cape2d[2]
		lfc = cape2d[3]
		if(_routines.need_mucape):
			xrOut["MUCAPE"] = (('south_north', 'west_east'), mucape)
		if(_routines.need_mucin):
			xrOut["MUCIN"] = (('south_north', 'west_east'), mucin)
		if(_routines.need_lcl):
			xrOut["LCL"] = (('south_north', 'west_east'), lcl)
		if(_routines.need_lfc):
			xrOut["LFC"] = (('south_north', 'west_east'), lfc)
		del(cape2d)
		del(mucape)
		del(mucin)
		del(lcl)
		del(lfc)
	##
	## - Storm Relative Helicity		
	if(_routines.need_srh):
		print("SRH - " + str(ncFile_Name))
		for l in _routines.srh_levels:
			srh = Calculation.get_srh(daskArray, top=l, omp_threads=dask_threads, num_workers=dask_nodes)
			xrOut["SRH_" + str(l)] = (('south_north', 'west_east'), srh)
			del(srh)
	##
	## - Updraft Helicity				
	if(_routines.need_uphel):
		print("UPHL - " + str(ncFile_Name))
		if(len(_routines.updft_helcy_levels) % 2 != 0):
			logger.write("***WARNING*** Error in updraft helicity levels, list must have a divisible number of 2 (values are pairs).")
		else:
			lows = _routines.updft_helcy_levels[0::2]
			highs = _routines.updft_helcy_levels[1::2]
			for i in range(0, len(lows)):
				uphel = Calculation.get_udhel(daskArray, bottom=lows[i], top=highs[i], omp_threads=dask_threads, num_workers=dask_nodes)
				xrOut["UPHEL_" + str(lows[i]) + "_" + str(highs[i])] = (('south_north', 'west_east'), uphel)
				del(uphel)
	##
	## - Wind Shear
	if(_routines.need_shear):	
		print("WSHR - " + str(ncFile_Name))
		for l in _routines.shear_levels:			
			uS, vS, spd = Calculation.get_wind_shear(daskArray, top=l, omp_threads=dask_threads, num_workers=dask_nodes, z=z_vert)
			xrOut["SHEAR_U_" + str(l)] = (('south_north', 'west_east'), uS[0])
			xrOut["SHEAR_V_" + str(l)] = (('south_north', 'west_east'), vS[0])
			xrOut["SHEAR_MAG_" + str(l)] = (('south_north', 'west_east'), spd[0]) 
			del(uS)
			del(vS)
			del(spd)
	##
	## - AFWA Hail Diagnostic
	if(_routines.need_afwa_hail):			
		afwaHail = ArrayTools.fetch_variable(daskArray, "AFWA_HAIL")
		xrOut["AFWA_HAIL"] = (('south_north', 'west_east'), afwaHail)
		del(afwaHail)			
	##
	## - AFWA Tornado Diagnostic
	if(_routines.need_afwa_tor):			
		afwaTor = ArrayTools.fetch_variable(daskArray, "AFWA_TORNADO")
		xrOut["AFWA_TORNADO"] = (('south_north', 'west_east'), afwaTor)
		del(afwaTor)	
	##
	## - Done Calculations
	##
	# Save our variables to the output file.
	print("Saving output file.")
	timeOut = "0" + str(elapsedHours) if elapsedHours < 10 else str(elapsedHours)
	xrOut.to_netcdf(targetDir + "/WRFPRS_F" + timeOut + ".nc")
	#Done.
	return 0		
	
def run_plotting_routines(callObject):
	import Plotting
	import PyPostSettings
	import PyPostTools

	ncFile_Name = callObject['filename']
	_pySet = callObject['settings']
	targetDir = callObject['tDir']
	dask_threads = callObject['dask_threads']
	logger = PyPostTools.pyPostLogger()
	
	if(targetDir == ""):
		logger.write("Cannot run plotting routines, could not locate target directory.")
		return -1
	# Draw Plots
	if(_pySet["plot_surface_map"] == '1'):
		Plotting.plot_surface_map(daskArray, targetDir,
								  withTemperature = _pySet["plot_surface_map_temperature"] == '1', 
								  withWinds = _pySet["plot_surface_map_winds"] == '1', 
								  windScaleFactor = 75, 
								  withMSLP = _pySet["plot_surface_map_mslp"] == '1')
	if(_pySet["plot_simulated_reflectivity"] == '1'):
		Plotting.plot_simulated_reflectivity(daskArray, targetDir)
	if(_pySet["plot_precip_type"] == '1'):
		Plotting.plot_precipitation_type(daskArray, targetDir)
	if(_pySet["plot_accumulated_precip"] == '1'):
		Plotting.plot_accumulated_precip(daskArray, targetDir)
	if(_pySet["plot_accumulated_snowfall"] == '1'):
		Plotting.plot_accumulated_snowfall(daskArray, targetDir)
	if(_pySet["plot_precipitable_water"] == '1'):
		Plotting.plot_precipitable_water(daskArray, targetDir, 
										 withMSLP = _pySet["plot_precipitable_water_with_mslp_contours"] == '1')
	if(_pySet["plot_dewpoint_temperature"] == '1'):
		Plotting.plot_dewpoint_temperature(daskArray, targetDir, windScaleFactor = 75)
	if(_pySet["plot_surface_omega"] == '1'):
		Plotting.plot_surface_omega(daskArray, targetDir)
	if(_pySet["plot_10m_max_winds"] == '1'):
		Plotting.plot_10m_max_winds(daskArray, targetDir, windScaleFactor = 75)
	if(_pySet["plot_upper_lv_winds"] == '1'):
		Plotting.plot_upper_lv_winds(daskArray, targetDir, 
									 _pySet["upper_winds_levels"], 
									 windScaleFactor = 75, 
									 withHeights = _pySet["plot_upper_lv_winds_withheights"] == '1')
	if(_pySet["plot_theta_e"] == '1'):
		Plotting.plot_theta_e(daskArray, targetDir, 
							  _pySet["theta_e_levels"], 
							  withHeights = _pySet["plot_theta_e_heights"] == '1', 
							  withWinds = _pySet["plot_theta_e_winds"] == '1', 
							  windScaleFactor = 75)
	return 0
		
# Run the program.
if __name__ == "__main__":
	launch_python_post()