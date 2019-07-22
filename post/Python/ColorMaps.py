#!/usr/bin/python
# ColorMaps.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This file defines colormaps used with the plotting scripts
#  Most were created from this page:
#  http://www.strangeplanet.fr/work/gradient-generator/index.php

import matplotlib

std_temp_colors = ["#13915A", # <-25
				   "#11EC8D", # -25 - -20
				   "#ABF6DF", # -20 - -15
				   "#D8FFEF", # -15 - -10
				   "#5BFFFF", # -10 - -5
				   "#4CB7B7", # -5 - 0
				   "#E768FF", # 0 - 5
				   "#7733FF", # 5 - 10
				   "#542CA5", # 10 - 15
				   "#234C92", # 15 - 20
				   "#2B68D1", # 20 - 25
				   "#639BFC", # 25 - 30
				   "#06FCFC", # 30 - 35
				   "#12FFE0", # 35 - 40
				   "#0CF277", # 40 - 45
				   "#0FB55C", # 45 - 50
				   "#188D4F", # 50 - 55
				   "#99FF32", # 55 - 60
				   "#D2FF52", # 60 - 65
				   "#F1FF21", # 65 - 70
				   "#EFFF00", # 70 - 75
				   "#FFC400", # 75 - 80
				   "#FFDA5E", # 80 - 85
				   "#FFB662", # 85 - 90
				   "#E47900", # 90 - 95
				   "#FF5E52", # 95 - 100
				   "#FC1B0B", # 100 - 105
				   "#80160E", # 105 - 110
				   "#AF7672", # 110 - 115
				   "#E1D7D7"] # 115+
temp_colormap = matplotlib.colors.ListedColormap(std_temp_colors)

relvort_colors = ["#575457", 
				  "#5D595D", 
				  "#645E64", 
				  "#6B636B", 
				  "#79767B", 
				  "#88898B", 
				  "#979C9C", 
				  "#A6ABAB", 
				  "#B5BABA", 
				  "#C5C9C9", 
				  "#D8DBDB", 
				  "#EBEDED", 
				  "#FFFFFF", 
				  "#BEFDFB", 
				  "#7DFBF7", 
				  "#3CFAF4", 
				  "#3FFBC7", 
				  "#42FD9A", 
				  "#45FF6D", 
				  "#83FD63", 
				  "#C1FB59", 
				  "#FFF94F", 
				  "#F8BB4A", 
				  "#F17E45", 
				  "#EB4141", 
				  "#F14A80", 
				  "#F853BF", 
				  "#FF5CFF", 
				  "#FF9BFF", 
				  "#FFDBFF"]
relvort_colormap = matplotlib.colors.ListedColormap(relvort_colors)

accum_precip_colors = ["#04E9E7",
					   "#019FF4",
					   "#0300F4",
					   "#02FD02",
					   "#01C501",
					   "#008E00",
					   "#FDF802",
					   "#E5BC00",
					   "#FD9500",
					   "#FD0000",
					   "#D40000",
					   "#BC0000",
					   "#F800FD",
					   "#9854C6",
					   "#FDFDFD"]
accum_precip_colormap = matplotlib.colors.ListedColormap(accum_precip_colors)

sim_reflec_colors = ["#FFFFFF",
					 "#808080",
					 "#00FFFF",
					 "#00BFFF",
					 "#0000FF",
					 "#00FF00",
					 "#32CD32",
					 "#008000",
					 "#FFFF00",
					 "#DAA520", 
					 "#FFA500",
					 "#FF0000",
					 "#8B0000",
					 "#800000",
					 "#FF00FF",
					 "#8A2BE2",
					 "#FFFFFF"]
sim_reflec_colormap = matplotlib.colors.ListedColormap(sim_reflec_colors)

snow_colors = ["#FFFFFF", 
			   "#C2BFFF", 
			   "#867FFF", 
			   "#493FFF", 
			   "#0D00FF", 
			   "#0C3FBF", 
			   "#0B7F7F", 
			   "#0ABF3F", 
			   "#09FF00", 
			   "#46E800", 
			   "#84D200", 
			   "#C1BC00", 
			   "#FFA600", 
			   "#FF7C00", 
			   "#FF5300", 
			   "#FF2900", 
			   "#FF0000", 
			   "#FF004E", 
			   "#FF009C", 
			   "#FF00EA"]
snow_colormap = matplotlib.colors.ListedColormap(snow_colors)

wind_colors = ["#BB00FF", 
			   "#7C00FF", 
			   "#3E00FF", 
			   "#0000FF", 
			   "#0A3DC1", 
			   "#147A83", 
			   "#1FB845", 
			   "#62CF2E", 
			   "#A6E717", 
			   "#EAFF00", 
			   "#F47F00", 
			   "#FF0000"]
wind_colormap = matplotlib.colors.ListedColormap(wind_colors)