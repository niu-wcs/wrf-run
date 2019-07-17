#!/usr/bin/python
# Routines.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# Contains the class responsible for controlling the required fields

import datetime
from datetime import datetime
import time
import os
import glob
from ..scripts import Tools
import Calculation
import ArrayTools
import xarray
import gc
import dask.array as da
from dask.array import map_blocks
from dask.distributed import Client, progress, metrics, LocalCluster

# Routines: Class responsible for parsing the control file and flagging what calculation methods are needed.
class Routines():
	pySet = None
	logger = None
	dask_client = None
	dask_nodes = 0
	dask_threads = 0
	calculation_future = None
	startTime = None
	postDir = None
	targetDir = None	
	
	need_mslp = False
	need_sim_dbz = False
	need_ptype = False
	need_acum_pcp = False
	need_acum_sno = False
	need_prec_wat = False
	need_dewpoint = False
	need_RH = False
	need_Temp = False
	need_winds = False
	need_theta_e = False
	need_omega = False
	need_sfc_max_winds = False
	need_geoht = False
	need_relvort = False
	need_3d_cape = False
	need_3d_cin = False
	need_mucape = False
	need_mucin = False
	need_lcl = False
	need_lfc = False
	need_srh = False
	need_uphel = False
	need_shear = False
	need_afwa_hail = False
	need_afwa_tor = False
	temp_levels = []
	winds_levels = []
	geoht_levels = []
	theta_e_levels = []
	rh_levels = []
	updft_helcy_levels = []
	srh_levels = []
	shear_levels = []

	def __init__(self, pySettings, client):
		self.logger = Tools.loggedPrint.instance()	
		self.pySet = pySettings
		self.dask_client = client
		#
		try:
			nodes = os.environ["PYTHON_POST_NODES"]
			threads = os.environ["PYTHON_POST_THREADS"]
			start = os.environ["PYTHON_POST_FIRSTTIME"]
			
			self.dask_nodes = nodes
			self.dask_threads = threads
			self.startTime = datetime.strptime(start, '%Y%m%d%H')
		except KeyError:
			self.logger.write("Could not locate environment variables set by the original application (NODES/THREADS), check the logs to ensure it is being done.")
			self.logger.close()
			sys.exit("Failed to find environmental variable (NODES/THREADS), check original application to ensure it is being set.")			
		self.gatherRoutines()
		
	def gatherRoutines(self):
		# Scan each control file option available and set the respective flags.
		if(self.pySet.fetch("plot_surface_map_temperature") == '1'):
			self.need_Temp = True
			self.temp_levels.append(0)
		if(self.pySet.fetch("plot_surface_map_winds") == '1' 
			or self.pySet.fetch("plot_surface_rh_and_winds") == '1' 
			or self.pySet.fetch("plot_upper_lv_winds") == '1'
			or self.pySet.fetch("plot_theta_e_winds") == '1'
			or self.pySet.fetch("plot_rh_and_wind") == '1'):
			self.need_winds = True
			if(self.pySet.fetch("plot_surface_map_winds") == '1'):
				self.winds_levels.append(0)
			if(self.pySet.fetch("plot_upper_lv_winds")):
				self.winds_levels = self.iterative_add(self.winds_levels, self.pySet.fetch("upper_winds_levels"))
			if(self.pySet.fetch("plot_rh_and_wind")):
				self.winds_levels = self.iterative_add(self.winds_levels, self.pySet.fetch("rh_and_wind_levels"))
			if(self.pySet.fetch("plot_theta_e_winds")):
				self.winds_levels = self.iterative_add(self.winds_levels, self.pySet.fetch("theta_e_levels"))
		if(self.pySet.fetch("plot_surface_map_mslp") == '1'
			or self.pySet.fetch("plot_precipitable_water_with_mslp_contours") == '1'):	
			self.need_mslp = True
		if(self.pySet.fetch("plot_simulated_reflectivity") == '1'):
			self.need_sim_dbz = True
		if(self.pySet.fetch("plot_precip_type") == '1'):
			self.need_ptype = True
		if(self.pySet.fetch("plot_accumulated_precip") == '1'):
			self.need_acum_pcp = True
		if(self.pySet.fetch("plot_accumulated_snowfall") == '1'):
			self.need_acum_sno = True
		if(self.pySet.fetch("plot_precipitable_water") == '1'):
			self.need_prec_wat = True
		if(self.pySet.fetch("plot_dewpoint_temperature") == '1'):
			self.need_dewpoint = True
		if(self.pySet.fetch("plot_surface_omega") == '1'):
			self.need_omega = True
		if(self.pySet.fetch("plot_10m_max_winds") == '1'):
			self.need_sfc_max_winds = True
		if(self.pySet.fetch("plot_upper_lv_winds_withheights") == '1'
			or self.pySet.fetch("plot_theta_e_heights") == '1'
			or self.pySet.fetch("plot_500_rel_vort_withheights") == '1'):			
			self.need_geoht = True			
			if(self.pySet.fetch("plot_upper_lv_winds_withheights")):
				self.geoht_levels = self.iterative_add(self.geoht_levels, self.pySet.fetch("upper_winds_levels"))
			if(self.pySet.fetch("plot_theta_e_heights")):
				self.geoht_levels = self.iterative_add(self.geoht_levels, self.pySet.fetch("theta_e_levels"))
			if(self.pySet.fetch("plot_500_rel_vort_withheights")):
				self.geoht_levels = self.iterative_add(self.geoht_levels, [500])	
		if(self.pySet.fetch("plot_theta_e") == '1'):
			self.need_theta_e = True
			self.theta_e_levels = self.iterative_add(self.theta_e_levels, self.pySet.fetch("theta_e_levels"))
		if(self.pySet.fetch("plot_rh_and_wind") == '1'):
			self.need_RH = True
			self.rh_levels = self.iterative_add(self.rh_levels, self.fetch("rh_and_wind_levels"))
		if(self.pySet.fetch("plot_500_rel_vort") == '1'):
			self.need_relvort = True
		if(self.pySet.fetch("plot_CAPE") == '1'):
			self.need_3d_cape = True
		if(self.pySet.fetch("plot_MUCAPE") == '1'):
			self.need_mucape = True
		if(self.pySet.fetch("plot_MUCIN") == '1'):
			self.need_mucin = True		
		if(self.pySet.fetch("plot_LCL") == '1'):
			self.need_lcl = True	
		if(self.pySet.fetch("plot_LFC") == '1'):
			self.need_lfc = True				
		if(self.pySet.fetch("plot_CIN") == '1'):
			self.need_3d_cin = True
		if(self.pySet.fetch("plot_AFWA_Hail") == '1'):
			self.need_afwa_hail = True
		if(self.pySet.fetch("plot_AFWA_Tor") == '1'):
			self.need_afwa_tor = True
		if(self.pySet.fetch("plot_shear") == '1'):
			self.need_shear = True
			self.shear_levels = self.pySet.fetch("shear_levels")
		if(self.pySet.fetch("plot_srh") == '1'):
			self.need_srh = True
			self.srh_levels = self.pySet.fetch("srh_levels")
		if(self.pySet.fetch("plot_updft_helcy") == '1'):
			self.need_uphel = True			
			self.updft_helcy_levels = self.pySet.fetch("updft_helcy_levels")
			
	def iterative_add(self, inList, addList):
		resultList = inList
		for e in addList:
			if(e in inList):
				continue
			else:
				resultList.append(e)
		return resultList
		
	def start_calculations(self):
		try:
			self.postDir = os.environ["PYTHON_POST_DIR"]
			self.targetDir = os.environ["PYTHON_POST_TARG_DIR"]
		except KeyError:
			self.logger.write("Could not locate environment variables set by the original application (DIRS), check the logs to ensure it is being done.")
			self.logger.close()
			sys.exit("Failed to find environmental variable (DIRS), check original application to ensure it is being set.")		
			return False
		# Get the list of files
		logger.write("  - Collecting files from target directory (" + postDir + ").")
		fList = sorted(glob.glob(self.postDir + "wrfout*"))
		logger.write("  - " + len(fList) " files have been found, pushing run_calculation_routines() to dask.")
		self.calculation_future = self.dask_client.map(self.run_calculation_routines, ncFiles)
	
	def run_calculation_routines(self, ncFile_Name):
		daskArray = xarray.open_mfdataset(ncFile_name, parallel=True)
		forecastTime_str = ncFile_name[-19:]
		forecastTime = datetime.strptime(forecastTime_str, '%Y-%m-%d_%H_%M_%S')
		elapsedTime = forecastTime - self.startTime
		elapsedHours = elapsedTime.days*24 + elapsedTime.seconds//3600
		# Grab the vertical interpolation levels
		p_vert = get_full_p(daskArray)
		z_vert = get_height(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
		# Our end goal is to create a new xArray saving only what we need to it. Start by creaying a "blank" xarray
		xrOut = xarray(data=None)
		# Now, calculate the variables.
		##
		## - MSLP
		if(self.need_mslp):
			mslp = Calculation.get_slp(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["MSLP"] = mslp[0]
			del(mslp)
		##
		## - Simulated Radar Reflectivity			
		if(self.need_sim_dbz):
			dbz = Calculation.get_dbz(daskArray, use_varint=False, use_liqskin=False, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["DBZ"] = dbz[0]
			del(dbz)
		##
		## - Precipitation Type			
		if(self.need_ptype):
			# Need to make a routine for this.
			self.logger.write("Precipitation type is currently unsupported, ignoring.")
		##
		## - Total Accumulated Precipitation			
		if(self.need_acum_pcp):
			acum_pcp = Calculation.get_accum_precip(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["ACUM_PCP"] = acum_pcp[0]
			del(acum_pcp)
		##
		## - Total Accumulated Snowfall			
		if(self.need_acum_sno):
			acum_sno = ArrayTools.fetch_variable(daskArray, "SNOWNC")
			xrOut["ACUM_SNO"] = acum_sno
			del(acum_sno)
		##
		## - Precipitable Water			
		if(self.need_prec_wat):
			prec_wat = Calculation.get_pw(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["PW"] = prec_wat[0]
			del(prec_wat)
		##
		## - Dewpoint Temperature			
		if(self.need_dewpoint):
			td = Calculation.get_dewpoint(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["TD"] = td[0]
			del(td)
		##
		## - Relative Humidity			
		if(self.need_RH):	
			rh = Calculation.get_rh(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			for l in self.rh_levels:
				if(l == 0):
					xrOut["SFC_RH"] = rh[0]
				else:
					rh_level = wrapped_interplevel(rh, p_vert, l, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
					xrOut["RH_" + str(l)] = rh_level[0]
					del(rh_level)
			del(rh)		
		##
		## - Air Temperature			
		if(self.need_Temp):
			tk = Calculation.get_tk(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			for l in self.temp_levels:
				if(l == 0):
					xrOut["SFC_T"] = tk[0]
				else:
					tk_level = wrapped_interplevel(tk, p_vert, l, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
					xrOut["T_" + str(l)] = tk_level[0]
					del(tk_level)
			del(tk)
		##
		## - U/V Wind Components			
		if(self.need_winds):
			for(l in self.winds_levels):
				# We can handle the 0 as surface here because this function defaults to surface winds when requested_top == 0
				u, v = Calculation.get_winds_at_level(daskArray, vertical_field=p_vert, requested_top=l)
				if(l == 0):
					xrOut["SFC_U"] = u
					xrOut["SFC_V"] = v
				else:
					xrOut["U_" + str(l)] = u[0]
					xrOut["V_" + str(l)] = v[0]
		##
		## - Equivalent Potential Temperature (Theta_E)					
		if(self.need_theta_e):
			eth = Calculation.get_eth(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			for l in self.theta_e_levels:
				if(l == 0):
					xrOut["SFC_THETA_E"] = eth[0]
				else:
					eth_level = wrapped_interplevel(eth, p_vert, l, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
					xrOut["THETA_E_" + str(l)] = eth_level[0]
					del(eth_level)
			del(eth)
		##
		## - Omega			
		if(self.need_omega):
			omega = Calculation.get_omega(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			xrOut["OMEGA"] = omega[0]
			del(omega)
		##
		## - Max Surface Wind Gust (AFWA Diagnostic)			
		if(self.need_sfc_max_winds):
			maxWind = ArrayTools.fetch_variable(daskArray, "WSPD10MAX")
			xrOut["MAX_WIND_SFC"] = maxWind
			del(maxWind)
		##
		## - Geopotential Height			
		if(self.need_geoht):
			for l in self.geoht_levels:
				z_level = wrapped_interplevel(z_vert, p_vert, l, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
				xrOut["GEOHT_" + str(l)] = z_level[0]
				del(z_level)	
		##
		## - 500 mb Relative Vorticity			
		if(self.need_relvort):
			rvo = get_rvor(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
			rvo_500 = wrapped_interplevel(rvo, p_vert, 500, omp_threads=self.dask_threads, num_workers=self.dask_nodes) 
			xrOut["RVO_500"] = rvo_500
			del(rvo)
			del(rvo_500)
		##
		## - Convective Available Potential Energy (3D) & Convective Inhibition (3D)			
		if(self.need_3d_cape or self.need_3d_cin):
			cape3d = Calculation.get_cape3d(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			cape = cape3d[0]
			cin = cape3d[1]
			if(self.need_3d_cape):
				xrOut["CAPE_3D"] = cape
			if(self.need_3d_cin):
				xrOut["CIN_3D"] = cin
			del(cape3d)
			del(cape)
			del(cin)
		##
		## - Maximum Cape (MUCAPE, 2D), Maximum CIN (MUCIN, 2D), Lifting Condensation Level (LCL), Level of Free Convection (LFC)			
		if(self.need_mucape or self.need_mucin or self.need_lcl or self.need_lfc):		
			cape2d = Calculation.get_cape2d(daskArray, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
			mucape = cape2d[0]
			mucin = cape2d[1]
			lcl = cape2d[2]
			lfc = cape2d[3]
			if(self.need_mucape):
				xrOut["MUCAPE"] = mucape
			if(self.need_mucin):
				xrOut["MUCIN"] = mucin
			if(self.need_lcl):
				xrOut["LCL"] = lcl
			if(self.need_lfc):
				xrOut["LFC"] = lfc
			del(cape2d)
			del(mucape)
			del(mucin)
			del(lcl)
			del(lfc)
		##
		## - Storm Relative Helicity		
		if(self.need_srh):
			for l in self.srh_levels:
				srh = Calculation.get_srh(daskArray, top=l, omp_threads=self.dask_threads, num_workers=self.dask_nodes)
				xrOut["SRH_" + str(l)] = srh
				del(srh)
		##
		## - Updraft Helicity				
		if(self.need_uphel):
			if(len(self.updft_helcy_levels) % 2 != 0):
				self.logger.write("Error in updraft helicity levels, list must have a divisible number of 2 (values are pairs).")
			else:
				lows = self.updft_helcy_levels[0::2]
				highs = self.updft_helcy_levels[1::2]
				for i in range(0, len(lows)):
					uphel = Calculation.get_udhel(daskArray, bottom=lows[i], top=highs[i], omp_threads=self.dask_threads, num_workers=self.dask_nodes)
					xrOut["UPHEL_" + lows[i] + "_" + highs[i]] = uphel
					del(uphel)
		##
		## - Wind Shear
		if(self.need_shear):	
			for l in self.shear_levels:			
				uS, vS, spd = Calculation.get_wind_shear(daskArray, top=l, omp_threads=self.dask_threads, num_workers=self.dask_nodes, z=z_vert)
				xrOut["SHEAR_U_" + str(l)] = uS[0]
				xrOut["SHEAR_V_" + str(l)] = vS[0]
				xrOut["SHEAR_MAG_" + str(l)] = spd[0] 
				del(uS)
				del(vS)
				del(spd)
		##
		## - AFWA Hail Diagnostic
		if(self.need_afwa_hail):			
			afwaHail = ArrayTools.fetch_variable(daskArray, "AFWA_HAIL")
			xrOut["AFWA_HAIL"] = afwaHail
			del(afwaHail)			
		##
		## - AFWA Tornado Diagnostic
		if(self.need_afwa_tor):			
			afwaTor = ArrayTools.fetch_variable(daskArray, "AFWA_TORNADO")
			xrOut["AFWA_TORNADO"] = afwaTor
			del(afwaTor)	
		##
		## - Done Calculations
		##
		# Save our variables to the output file.
		timeOut = "0" + str(elapsedHours) if elapsedHours < 10 else str(elapsedHours)
		xrOut.to_netcdf(self.targetDir + "/WRFPRS_F" + timeOut + ".nc")
		#Done.
		return True