#!/usr/bin/python
# PythonPost.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This is the main python file called by the post-processing job and handles the parallel
#  processing on the wrfout files.

import os
import glob
#from ..scripts import Tools
import PyPostTools
import Calculation
import ArrayTools
import PyPostSettings
import Routines
import xarray
import dask.array as da
from dask.array import map_blocks
from dask.distributed import Client, progress, metrics, LocalCluster, wait
from datetime import datetime

dask_client = None
dask_nodes = 0
dask_threads = 0

_routines = None
_pySet = None

def launch_python_post():
	curDir = os.path.dirname(os.path.abspath(__file__)) 
	logger = PyPostTools.pyPostLogger.instance()

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
	except KeyError:
		logger.write("***FAIL*** KeyError encountered while trying to access important environmental variables, abort.")
		sys.exit("")
	logger.write("  - Success!")
	logger.write("  - Initializing Dask Client (" + str(dask_nodes) + " Nodes Requested), Collecting routines needed")
	cluster = LocalCluster(n_workers=dask_nodes)
	dask_client = Client(cluster)
	_routines = Routines.Routines(_pySet)
	logger.write("  - Success!")
	logger.write(" 1. Done.")
	logger.write(" 2. Start Post-Processing Calculations")
	calculation_future = start_calculations(dask_client)
	wait(calculation_future) 
	logger.write(" 2. Done.")
	logger.write(" 3. Generating Figures")
	plotting_future = start_plotting(dask_client)
	logger.write(" 3. Done.")
	logger.write(" 4. Final Steps")
	
	logger.write(" 4. Done.")
	logger.write("All Steps Completed.")
	logger.write("***SUCCESS*** Program execution complete.")
	logger.close()	

def start_calculations(dask_client):	
	logger = PyPostTools.pyPostLogger.instance()

	try:
		postDir = os.environ["PYTHON_POST_DIR"]
	except KeyError:
		logger.write("***FAIL*** Could not locate environment variables set by the original application (DIRS), check the logs to ensure it is being done.")
		logger.close()
		sys.exit("Failed to find environmental variable (DIRS), check original application to ensure it is being set.")		
		return False
	# Get the list of files
	logger.write("  - Collecting files from target directory (" + postDir + ").")
	fList = sorted(glob.glob(postDir + "wrfout*"))
	logger.write("  - " + str(len(fList)) + " files have been found, pushing run_calculation_routines() to dask.")
	calculation_future = dask_client.map(run_calculation_routines, fList)
	return calculation_future
	
def run_calculation_routines(ncFile_Name):
	logger = PyPostTools.pyPostLogger.instance()
	try:
		start = os.environ["PYTHON_POST_FIRSTTIME"]
		targetDir = os.environ["PYTHON_POST_TARG_DIR"]
	except KeyError:
		logger.write("***FAIL*** Could not locate environment variables set by the original application (FIRSTTIME), check the logs to ensure it is being done.")
		logger.close()
		sys.exit("Failed to find environmental variable (FIRSTTIME), check original application to ensure it is being set.")		
		return False
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
	# Copy map information first
	xrOut.coords["XLAT"] = (('south_north', 'west_east'), daskArray["XLAT"][0])
	xrOut.coords["XLONG"] = (('south_north', 'west_east'), daskArray["XLONG"][0])		
	# Now, calculate the variables.
	##
	## - MSLP
	if(_routines.need_mslp):
		mslp = Calculation.get_slp(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["MSLP"] = (('south_north', 'west_east'), mslp)
		del(mslp)
	##
	## - Simulated Radar Reflectivity			
	if(_routines.need_sim_dbz):
		dbz = Calculation.get_dbz(daskArray, use_varint=False, use_liqskin=False, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["DBZ"] = (('south_north', 'west_east'), dbz[0])
		del(dbz)
	##
	## - Precipitation Type			
	if(_routines.need_ptype):
		# Need to make a routine for this.
		logger.write("***WARNING*** Precipitation type is currently unsupported, ignoring.")
	##
	## - Total Accumulated Precipitation			
	if(_routines.need_acum_pcp):
		acum_pcp = Calculation.get_accum_precip(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["ACUM_PCP"] = (('south_north', 'west_east'), acum_pcp[0])
		del(acum_pcp)
	##
	## - Total Accumulated Snowfall			
	if(_routines.need_acum_sno):
		acum_sno = ArrayTools.fetch_variable(daskArray, "SNOWNC")
		xrOut["ACUM_SNO"] = (('south_north', 'west_east'), acum_sno)
		del(acum_sno)
	##
	## - Precipitable Water			
	if(_routines.need_prec_wat):
		prec_wat = Calculation.get_pw(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["PW"] = (('south_north', 'west_east'), prec_wat)
		del(prec_wat)
	##
	## - Dewpoint Temperature			
	if(_routines.need_dewpoint):
		td = Calculation.get_dewpoint(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["TD"] = (('south_north', 'west_east'), td[0])
		del(td)
	##
	## - Relative Humidity			
	if(_routines.need_RH):	
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
		omega = Calculation.get_omega(daskArray, omp_threads=dask_threads, num_workers=dask_nodes)
		xrOut["OMEGA"] = (('south_north', 'west_east'), omega[0])
		del(omega)
	##
	## - Max Surface Wind Gust (AFWA Diagnostic)			
	if(_routines.need_sfc_max_winds):
		maxWind = ArrayTools.fetch_variable(daskArray, "WSPD10MAX")
		xrOut["MAX_WIND_SFC"] = (('south_north', 'west_east'), maxWind)
		del(maxWind)
	##
	## - Geopotential Height			
	if(_routines.need_geoht):
		for l in _routines.geoht_levels:
			z_level = ArrayTools.wrapped_interplevel(z_vert, p_vert, l, omp_threads=dask_threads, num_workers=dask_nodes) 
			xrOut["GEOHT_" + str(l)] = (('south_north', 'west_east'), z_level[0])
			del(z_level)	
	##
	## - 500 mb Relative Vorticity			
	if(_routines.need_relvort):
		rvo = get_rvor(daskArray, omp_threads=dask_threads, num_workers=dask_nodes) 
		rvo_500 = ArrayTools.wrapped_interplevel(rvo, p_vert, 500, omp_threads=dask_threads, num_workers=dask_nodes) 
		xrOut["RVO_500"] = (('south_north', 'west_east'), rvo_500)
		del(rvo)
		del(rvo_500)
	##
	## - Convective Available Potential Energy (3D) & Convective Inhibition (3D)			
	if(_routines.need_3d_cape or _routines.need_3d_cin):
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
		for l in _routines.srh_levels:
			srh = Calculation.get_srh(daskArray, top=l, omp_threads=dask_threads, num_workers=dask_nodes)
			xrOut["SRH_" + str(l)] = (('south_north', 'west_east'), srh)
			del(srh)
	##
	## - Updraft Helicity				
	if(_routines.need_uphel):
		if(len(_routines.updft_helcy_levels) % 2 != 0):
			logger.write("***WARNING*** Error in updraft helicity levels, list must have a divisible number of 2 (values are pairs).")
		else:
			lows = _routines.updft_helcy_levels[0::2]
			highs = _routines.updft_helcy_levels[1::2]
			for i in range(0, len(lows)):
				uphel = Calculation.get_udhel(daskArray, bottom=lows[i], top=highs[i], omp_threads=dask_threads, num_workers=dask_nodes)
				xrOut["UPHEL_" + lows[i] + "_" + highs[i]] = (('south_north', 'west_east'), uphel)
				del(uphel)
	##
	## - Wind Shear
	if(_routines.need_shear):	
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
	timeOut = "0" + str(elapsedHours) if elapsedHours < 10 else str(elapsedHours)
	xrOut.to_netcdf(targetDir + "/WRFPRS_F" + timeOut + ".nc")
	#Done.
	return True		
		
# Run the program.
if __name__ == "__main__":
	launch_python_post()