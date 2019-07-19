#!/usr/bin/python
# ArrayTools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance grants some additional array tool support for handling
#  NumPy & Dask interactions that may not be supported by wrf-python's implementations
#  out-of-box. Functions in this class are named wrapped_name with name being the same
#  as the original wrf-python implementation

import numpy as np
import dask.array as da
from wrf.constants import default_fill

#wrapped_destagger() - A wrapper method that handles the wrf-python destagger() function, safe for Dask
def wrapped_destagger(daskArray, stagger_dim):
    shape = daskArray.shape
    dims = daskArray.ndim
    dim_size = shape[stagger_dim]

    full_slice = slice(None)
    slice1 = slice(0, dim_size - 1, 1)
    slice2 = slice(1, dim_size, 1)

    # default to full slices
    dim_ranges_1 = [full_slice] * dims
    dim_ranges_2 = [full_slice] * dims

    # for the stagger dim, insert the appropriate slice range
    dim_ranges_1[stagger_dim] = slice1
    dim_ranges_2[stagger_dim] = slice2

    result = .5*(daskArray[tuple(dim_ranges_1)] + daskArray[tuple(dim_ranges_2)])
    return result
	
#wrapped_either() - A wrapper method that support's the wrf-python either() method for dask arrays
def wrapped_either(daskArray, varNames):
	for name in varNames:
		try:
			daskArray[name]
			return name
		except KeyError:
			continue
		
"""
This block of code allows you to use interplevel() on daskArrays via wrapped_interplevel
 NOTE: At the moment it returns the [time] index as the first array index, so calling out[0] is how
  you extract the 2D field.
"""
def wrapped_interpz3d(field3d, z, desiredloc, missingval, outview=None, omp_threads=1):
	from wrf.extension import _interpz3d, omp_set_num_threads

	omp_set_num_threads(omp_threads)
	result = _interpz3d(field3d, z, desiredloc, missingval, outview)

	return result
	
def wrapped_interpz3d_lev2d(field3d, z, lev2d, missingval, outview=None, omp_threads=1):
	from wrf.extension import _interpz3d_lev2d, omp_set_num_threads

	omp_set_num_threads(omp_threads)
	result = _interpz3d_lev2d(field3d, z, lev2d, missingval, outview)

	return result
	
def wrapped_interplevel(field3d, vert, desiredlev, missing=default_fill(np.float64), omp_threads=1):
	from wrf.extension import omp_set_num_threads
	import numpy.ma as ma
	from dask.array import map_blocks	

	omp_set_num_threads(omp_threads)
	dtype = field3d.dtype

	_desiredlev = da.asarray(desiredlev)
	if _desiredlev.ndim == 0:
		_desiredlev = da.array([desiredlev], np.float64)
		levsare2d = False
	else:
		levsare2d = _desiredlev.ndim >= 2

	if not levsare2d:
		result = map_blocks(wrapped_interpz3d, field3d, vert, _desiredlev, missing, omp_threads=omp_threads, dtype=dtype)
	else:
		result = map_blocks(wrapped_interpz3d_lev2d, field3d, vert, _desiredlev, missing, omp_threads=omp_threads, dtype=dtype)

	masked = ma.masked_values(result, missing)
	return masked
            
# Wrapped version of _lat_varname
def wrapped_lat_varname(daskArray, stagger):
	if stagger is None or stagger.lower() == "m":
		varname = wrapped_either(daskArray, ("XLAT", "XLAT_M"))
	elif stagger.lower() == "u" or stagger.lower() == "v":
		varname = "XLAT_{}".format(stagger.upper())
	else:
		raise ValueError("invalid 'stagger' value")

	return varname    

# Wrapped version of _lon_varname
def wrapped_lon_varname(daskArray, stagger):
    if stagger is None or stagger.lower() == "m":
        varname = wrapped_either(daskArray, ("XLONG", "XLONG_M"))
    elif stagger.lower() == "u" or stagger.lower() == "v":
        varname = "XLONG_{}".format(stagger.upper())
    else:
        raise ValueError("invalid 'stagger' value")

    return varname 	
	
# fetch_variable() is used to access variables in the netCDF file
def fetch_variable(daskArray, varName, include_time=False, include_meta=False):
	try:
		subArray = daskArray[varName]
	except KeyError:
		raise KeyError("Invalid key. " + varName + " is not found.")
		
	if(include_meta):
		subArray2 = subArray
	else:
		subArray2 = subArray.data
		
	return subArray2 if include_time else subArray2.squeeze()