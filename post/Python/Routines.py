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

# Routines: Class responsible for parsing the control file and flagging what calculation methods are needed.
class Routines():
	pySet = None
	logger = None	
	
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

	def __init__(self, pySettings):
		self.pySet = pySettings		
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