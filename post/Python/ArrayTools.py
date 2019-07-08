#!/usr/bin/python
# ArrayTools.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance grants some additional array tool support for handling
#  NumPy & Dask interactions that may not be supported out-of-the-box

import numpy as np
import dask.array as da

#wrapped_unstagger() - A wrapper method that handles the wrf-python destagger function(), safe for Dask
def wrapped_unstagger(daskArray, stagger_dim, num_workers=1, save_numpy=False):
	numpy_array = to_np(daskArray, num_workers)

    shape = numpy_array.shape
    dims = numpy_array.ndim
    dim_size = numpy_array[stagger_dim]	
	
    full_slice = slice(None)
    slice1 = slice(0, stagger_dim_size - 1, 1)
    slice2 = slice(1, stagger_dim_size, 1)

    # default to full slices
    dim_ranges_1 = [full_slice] * num_dims
    dim_ranges_2 = [full_slice] * num_dims

    # for the stagger dim, insert the appropriate slice range
    dim_ranges_1[stagger_dim] = slice1
    dim_ranges_2[stagger_dim] = slice2

    result = .5*(numpy_array[tuple(dim_ranges_1)] + numpy_array[tuple(dim_ranges_2)])

	if(save_numpy):
		return result
	return da.from_array(result)

# NOTE: Try to limit these calls as trying to convert to a np array will invoke the calculation routine.
def to_np(DaskArray, num_workers=1):
	return np.array(DaskArray.compute(num_workers))
	
def to_da(numpyArray):
	return da.from_array(numpyArray)