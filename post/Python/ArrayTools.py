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