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
	
def plot_surface_map(ncFile, targetDir, withTemperature=True, withWinds=True, windScaleFactor = 50, withMSLP = True):
	logger = PyPostTools.pyPostLogger()
	if(withTemperature == False and withWinds == False and withMSLP == False):
		logger.write("Error in plot_surface_map(): Nothing to do.")
		return False
	fig, ax, X, Y = prepare_plot_object(ncFile)
	st, fh, fh_int = getTimeObjects(ncFile)
	
	titleAdd = ""
	if(withTemperature):
		T = ncFile["SFC_T"]
		TF = ((T - 273.15) * 9/5) + 32
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
		titleAdd += "MSLP "
	
	if(withWinds):
		u = ncFile["SFC_U"]
		v = ncFile["SFC_V"]
		plt.barbs(to_np(X[::windScaleFactor,::windScaleFactor]), to_np(Y[::windScaleFactor,::windScaleFactor]), 
			to_np(u[::windScaleFactor, ::windScaleFactor]), to_np(v[::windScaleFactor, ::windScaleFactor]), 
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