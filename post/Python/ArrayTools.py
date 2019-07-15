#!/usr/bin/python
# ArrayTools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance grants some additional array tool support for handling
#  NumPy & Dask interactions that may not be supported out-of-the-box

import numpy as np
import dask.array as da

#wrapped_unstagger() - A wrapper method that handles the wrf-python destagger function(), safe for Dask
def wrapped_unstagger(daskArray, stagger_dim):
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
            
def wrapped_lat_varname(daskArray, stagger):
    if stagger is None or stagger.lower() == "m":
        varname = wrapped_either(daskArray, ("XLAT", "XLAT_M"))
    elif stagger.lower() == "u" or stagger.lower() == "v":
        varname = "XLAT_{}".format(stagger.upper())
    else:
        raise ValueError("invalid 'stagger' value")

    return varname    

def wrapped_lon_varname(daskArray, stagger):
    if stagger is None or stagger.lower() == "m":
        varname = wrapped_either(daskArray, ("XLONG", "XLONG_M"))
    elif stagger.lower() == "u" or stagger.lower() == "v":
        varname = "XLONG_{}".format(stagger.upper())
    else:
        raise ValueError("invalid 'stagger' value")

    return varname 	