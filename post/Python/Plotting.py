#!/usr/bin/python
# Plotting.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This file defines plotting functions and routines

from netCDF4 import Dataset
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature
from scipy.ndimage.filters import gaussian_filter
import numpy as np
import ColorMaps
import PyPostTools
import Conversions
import os
from datetime import datetime, timedelta
from wrf import to_np

def get_projection_object(ncFile):
    # Cartopy has a "globe" object to define more projection standards, we create this first
    globe = ccrs.Globe(ellipse=None,
                       semimajor_axis=6370000,
                       semiminor_axis=6370000,
                       nadgrids="@null")    
    # Now we can create the projection object
    cen_lat  = float(ncFile.MOAD_CEN_LAT)
    cen_lon  = float(ncFile.CEN_LON)
    std_pll  = [ncFile.TRUELAT1] # We need a list object, so we'll contain it in a list
    cutoff   = -30.0
    projObj = ccrs.LambertConformal(central_latitude=cen_lat, 
                                    central_longitude=cen_lon,
                                    standard_parallels=std_pll,
                                    globe=globe,
                                    cutoff=cutoff)
    
    return projObj

def getGrid(ncFile, no_time=True): 
    if(no_time):
        try:
            lats = ncFile["XLAT"]
        except KeyError:
            raise ValueError("XLAT not found")
        try:
            lons = ncFile["XLONG"]
        except KeyError:
            raise ValueError("XLONG not found")    
    else:
        try:
            lats = ncFile["XLAT"][0]
        except KeyError:
            raise ValueError("XLAT not found")
        try:
            lons = ncFile["XLONG"][0]
        except KeyError:
            raise ValueError("XLONG not found")

    return lats, lons
	
# This function prepares a standard frame for the plot object (This is used by all plots)
def prepare_plot_object(ncFile):
	cart_proj = get_projection_object(ncFile) 
	fig = plt.figure(figsize=(12,9))
	ax = plt.axes(projection=cart_proj)
	
	Y, X = getGrid(ncFile, no_time=True)

	states = NaturalEarthFeature(category="cultural", scale="110m",
								 facecolor="none",
								 name="admin_1_states_provinces_lakes")	
	
	ax.add_feature(states, edgecolor="black", linestyle=':')
	ax.coastlines()
	return fig, ax, X, Y
	
# This function collects the initialization and forecast time objects
def getTimeObjects(ncFile):
	start = ncFile.STARTTIME
	fHour = ncFile.FORECASTHOUR
	fHourInt = int(fHour)
	
	startTime = datetime.strptime(start, '%Y%m%d%H')
	forecastTime = startTime + timedelta(hours=fHourInt)
	
	return startTime, forecastTime, fHourInt
	
def plot_surface_map(ncFile, targetDir, withTemperature = True, withWinds = True, windScaleFactor = 50, withMSLP = True):
	logger = PyPostTools.pyPostLogger()
	if(withTemperature == False and withWinds == False and withMSLP == False):
		logger.write("Error in plot_surface_map(): Nothing to do.")
		return False
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)
	
	titleAdd = ""
	if(withTemperature):
		T = ncFile["SFC_T"]
		TF = Conversions.K_to_F(T)
		clevs = np.arange(-30, 115, 5)
		contours = plt.contourf(X, Y, TF, clevs, cmap=ColorMaps.temp_colormap, transform=ccrs.PlateCarree())    
		cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
		cbar.set_label("Temperature (F)") 
		titleAdd += "Temperature "
	
	if(withMSLP):
		SLP = to_np(ncFile["MSLP"])
		smooth_slp = gaussian_filter(SLP, sigma=3)
		levs = np.arange(950, 1050, 4)
		linesC = plt.contour(X, Y, smooth_slp, levs, colors="black", transform=ccrs.PlateCarree(), linewidths = 1)	
		plt.clabel(linesC, inline=1, fontsize=10, fmt="%i")
		titleAdd += "MSLP (mb) "
	
	if(withWinds):
		u = ncFile["SFC_U"]
		v = ncFile["SFC_V"]
		
		uKT = Conversions.ms_to_kts(u)
		vKT = Conversions.ms_to_kts(v)
		plt.barbs(to_np(X[::windScaleFactor,::windScaleFactor]), to_np(Y[::windScaleFactor,::windScaleFactor]), 
			to_np(uKT[::windScaleFactor, ::windScaleFactor]), to_np(vKT[::windScaleFactor, ::windScaleFactor]), 
			transform=ccrs.PlateCarree(), length=6)
		titleAdd += "Winds "
	# Finish things up, for the title crop off the extra comma at the end, add the time text, and save.
	titleAdd = titleAdd.replace(" ", ", ")
	titleAdd = titleAdd[:-2]
	plt.title("Surface Map (" + titleAdd + ")")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/sfcmap_F" + str(fh_int))
	plt.close(fig)
	return True
	
def plot_simulated_reflectivity(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)

	dBZ = ncFile["DBZ"]
	clevs = np.arange(0, 85, 5)
	norm = matplotlib.colors.BoundaryNorm(clevs, 17) # normalize levels  
	
	contours = plt.contourf(X, Y, dBZ, clevs, norm=norm, cmap=ColorMaps.sim_reflec_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Radar Reflectivity Factor (dBZ)") 
	
	plt.title("Simulated Radar Reflectivity")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/simdbz_F" + str(fh_int))
	plt.close(fig)
	return True	
	
def plot_precipitation_type(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	logger.write("Precipitation type is not implemented yet, ignoring call.")
	return False
	
def plot_accumulated_precip(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)

	PCP = ncFile["ACUM_PCP"]
	clevs = [0.1, 0.5, 1, 2, 5, 10, 15, 20, 30, 40, 50, 80, 100, 200, 300, 500] # Units of mm
	norm = matplotlib.colors.BoundaryNorm(clevs, 15)  
	
	contours = plt.contourf(X, Y, PCP, clevs, norm=norm, cmap=ColorMaps.accum_precip_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Accumulated Precipitation (mm)") 
	
	plt.title("Total Accumulated Precipitation")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/simacum_pcp_F" + str(fh_int))
	plt.close(fig)
	return True	
	
def plot_accumulated_snowfall(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)

	PCP = ncFile["ACUM_SNO"]
	clevs = [0, 0.5, 1, 2.5, 3, 4, 5, 8, 10, 15, 20, 30, 40, 50, 80, 100, 150, 200, 250, 500]
	norm = matplotlib.colors.BoundaryNorm(clevs, 19)  
	
	contours = plt.contourf(X, Y, PCP, clevs, norm=norm, cmap=ColorMaps.snow_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Accumulated Snowfall (mm)") 
	
	plt.title("Total Accumulated Snowfall")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/simacum_sno_F" + str(fh_int))
	plt.close(fig)
	return True	
	
def plot_precipitable_water(ncFile, targetDir, withMSLP = True):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)
	
	titleAdd = ""
	
	PW = ncFile["PW"]
	clevs = np.linspace(0, 3, 32)
	norm = matplotlib.colors.BoundaryNorm(clevs, 32) 

	contours = plt.contourf(X, Y, PW, clevs, norm=norm, cmap=ColorMaps.pw_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Precipitable Water (in)") 
	
	if(withMSLP):
		SLP = to_np(ncFile["MSLP"])
		smooth_slp = gaussian_filter(SLP, sigma=3)
		levs = np.arange(950, 1050, 4)
		linesC = plt.contour(X, Y, smooth_slp, levs, colors="black", transform=ccrs.PlateCarree(), linewidths = 1)	
		plt.clabel(linesC, inline=1, fontsize=10, fmt="%i")
		titleAdd += ", MSLP (mb)"
		
	plt.title("Precipitable Water (in)" + titleAdd)
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/PW_F" + str(fh_int))
	plt.close(fig)
	return True	

def plot_dewpoint_temperature(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)

	TD = ncFile["TD"]
	TD_F = Conversions.C_to_F(TD)
	clevs = np.linspace(-20, 85, 36)
	norm = matplotlib.colors.BoundaryNorm(clevs, 36) 

	contours = plt.contourf(X, Y, TD_F, clevs, norm=norm, cmap=ColorMaps.td_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Dewpoint Temperature ($^\circ$ F)") 
	
	u = ncFile["SFC_U"]
	v = ncFile["SFC_V"]
	
	uKT = Conversions.ms_to_kts(u)
	vKT = Conversions.ms_to_kts(v)
	plt.barbs(to_np(X[::windScaleFactor,::windScaleFactor]), to_np(Y[::windScaleFactor,::windScaleFactor]), 
		to_np(uKT[::windScaleFactor, ::windScaleFactor]), to_np(vKT[::windScaleFactor, ::windScaleFactor]), 
		transform=ccrs.PlateCarree(), length=6)	
		
	plt.title("Surface Dewpoint Temperature ($^\circ$ F), Winds (kts)")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/TD_F" + str(fh_int))
	plt.close(fig)
	return True	
	
def plot_surface_omega(ncFile, targetDir):
	logger = PyPostTools.pyPostLogger()
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)
	
	# Convert Pa to dPA
	omega = ncFile["OMEGA"] / 10
	clevs = [50, 33, 30, 27, 24, 21, 18, 15, 12, 9, 6, 3, 0, -3, -6, -9, -12, -15, -18, -21, -24, -27, -30, -33, -36,
				-39, -45, -51, -57, -63, -69] #dPa/s
	norm = matplotlib.colors.BoundaryNorm(clevs, 30)  
	
	contours = plt.contourf(X, Y, omega, clevs, norm=norm, cmap=ColorMaps.omega_colormap, transform=ccrs.PlateCarree())    
	cbar = plt.colorbar(ax=ax, orientation="horizontal", pad=.05)
	cbar.set_label("Omega (dPa / s)") 
	
	SLP = to_np(ncFile["MSLP"])
	smooth_slp = gaussian_filter(SLP, sigma=3)
	levs = np.arange(950, 1050, 4)
	linesC = plt.contour(X, Y, smooth_slp, levs, colors="black", transform=ccrs.PlateCarree(), linewidths = 1)	
	plt.clabel(linesC, inline=1, fontsize=10, fmt="%i")	
	
	plt.title("Surface Omega (dPa / s), MSLP (mb)")
	plt.text(0.02, -0.02, "Forecast Time: " + fh.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.text(0.7, -0.02, "Initialized: " + st.strftime("%Y-%m-%d %H:%M UTC"), ha='left', va='center', transform=ax.transAxes)
	plt.subplots_adjust(bottom = 0.1)
	plt.savefig(targetDir + "/sfc_omega_F" + str(fh_int))
	plt.close(fig)
	return True		