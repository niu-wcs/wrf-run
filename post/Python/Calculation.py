#!/usr/bin/python
# Calculation.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance handles the parallel calculation routines for dask
#  - Notes on how this implementation is handled is shown here:
#     https://github.com/NCAR/wrf-python/wiki/How-to-add-dask-support

import numpy as np
import np.ma as ma
from netCDF4 import Dataset
import dask.array as da
from dask.array import map_blocks
from wrf import Constants, ConversionFactors

class Calculation:

	# Empty method
	def __init__(self):
		# Nothing to be done here.
		
	# Wrapped call for simple addition
	def wrapped_add(self, base, add):
		return base + add	
		
	# Wrapped call for simple subtraction
	def wrapped_sub(self, base, sub):
		return base - sub
		
	# Wrapped call for simple multiplication
	def wrapped_mul(self, base, prod):
		return base * prod
	
	# Wrapped call for simple division
	def wrapped_div(self, base, div):
		return base / div
		
	"""
		This block of code is focused on handling the "gather" routines for specific variables
		
		These are wrapped calls to specific functions with omp support enabled to allow for multiprocessing
		 on the specific function calls.
	"""
	def slp_wrap(destag_ph, tk, full_p, qvapor, omp_threads=1):
		from wrf.extension import _slp, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _slp(destag_ph, tk, full_p, qvapor)

		return result	
	
	def tk_wrap(full_p, full_t, omp_threads=1):
		from wrf.extension import _tk, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _tk(full_p, full_t)

		return result

	def td_wrap(full_p, qvapor, omp_threads=1):
		from wrf.extension import _td, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _td(full_p, qvapor)

		return result		
		
	def tv_wrap(temp_k, qvapor, omp_threads=1):
		from wrf.extension import _tv, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _tv(temp_k, qvapor)

		return result		
		
	def wetbulb_wrap(full_p, tk, qv, omp_threads=1):
		from wrf.extension import _wetbulb, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _wetbulb(full_p, tk, qv)

		return result			
		
	def dbz_wrap(full_p, tk, qv, qr, qs, qg, sn0, ivarint, iliqskin, omp_threads=1):
		from wrf.extension import _dbz, omp_set_num_threads

		omp_set_num_threads(omp_threads)
		result = _dbz(full_p, tk, qv, qr, qs, qg, sn0, ivarint, iliqskin)

		return result
		
	def srh_wrap(u1, v1, z1, ter, lats, top, omp_threads=1):
		from wrf.extension import _srhel, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)
		result = _srhel(u1, v1, z1, ter, lats, top)
		
		return result

	def udhel_wrap(zp, mapfct, u, v, wstag, dx, dy, bottom, top, omp_threads=1):
		from wrf.extension import _udhel, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)
		result = _udhel(zp, mapfct, u, v, wstag, dx, dy, bottom, top)
		
		return result
		
	def cape_wrap(p_hpa, tk, qv, z, ter, psfc_hpa, missing, i3dflag, ter_follow, omp_threads=1):
		from wrf.extension import _cape, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)
		result = _cape(p_hpa, tk, qv, z, ter, psfc_hpa, missing, i3dflag, ter_follow)
		
		return result
	
	def omega_wrap(qv, tk, wa, full_p, omp_threads=1):
		from wrf.extension import _omega, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)	
		result = _omega(qv, tk, wa, full_p)
		
		return result
		
	def pw_wrap(full_p, tv, qv, ht, omp_threads=1):
		from wrf.extension import _pw, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)	
		result = _pw(full_p, tv, qv, ht)
		
		return result
		
	def rh_wrap(qvapor, full_p, tk, omp_threads=1):
		from wrf.extension import _rh, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)	
		result = _rh(qvapor, full_p, tk)
		
		return result	

	def avo_wrap(u, v, msfu, msfv, msfm, cor, dx, dy, omp_threads=1):
		from wrf.extension import _avo, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)	
		result = _avo(u, v, msfu, msfv, msfm, cor, dx, dy)
		
		return result
		
	def pvo_wrap(u, v, full_t, full_p, msfu, msfv, msfm, cor, dx, dy, omp_threads=1):
		from wrf.extension import _pvo, omp_set_num_threads
		
		omp_set_num_threads(omp_threads)	
		result = _pvo(u, v, msfu, msfv, msfm, cor, dx, dy)
		
		return result	
	
	"""
		This block of code handles the calculation functions themselves
	"""
	def get_tv(daskArray, omp_threads=1, num_workers=1):
		t = daskArray["T"]
		p = daskArray["P"]
		pb = daskArray["PB"]
		qv = daskArray["QVAPOR"]	

		full_t = map_blocks(wrapped_add, Constants.T_BASE, t, omp_threads, dtype=t.dtype)
		full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)
		tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
		tv = map_blocks(tv_wrap, tk, qv, omp_threads, dtype=p.dtype)
		return tv.compute(num_workers)	
		
	def get_tw(daskArray, omp_threads=1, num_workers=1):
		t = daskArray["T"]
		p = daskArray["P"]
		pb = daskArray["PB"]
		qv = daskArray["QVAPOR"]
		
		full_t = map_blocks(wrapped_add, Constants.T_BASE, t, omp_threads, dtype=t.dtype)
		full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
		tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
		tw = map_blocks(wetbulb_wrap, tk, qv, omp_threads, dtype=p.dtype)
		return tw.compute(num_workers)
		
	def get_cape3d(daskArray, omp_threads=1, num_workers=1):
		from wrf.destag import destagger
		
		missing = default_fill(np.float64)
		
		t = daskArray["T"]
		p = daskArray["P"]
		pb = daskArray["PB"]
		qv = daskArray["QVAPOR"]
		ph = daskArray["PH"]
		phb = daskArray["PHB"]
		ter = daskArray["HGT"]
		psfc = daskArray["PSFC"]

		full_t = map_blocks(wrapped_add, Constants.T_BASE, t, omp_threads, dtype=t.dtype)
		full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
		tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

		geopt = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
		geopt_unstag = destagger(geopt, -3)
		z = map_blocks(wrapped_div, geopt_unstag, Constants.G, omp_threads, dtype=ph.dtype)
		
		p_hpa = map_blocks(wrapped_mul, full_p, ConversionFactors.PA_TO_HPA, omp_threads, dtype=p.dtype)
		psfc_hpa = map_blocks(wrapped_mul, psfc, ConversionFactors.PA_TO_HPA, omp_threads, dtype=p.dtype)

		i3dflag = 1
		ter_follow = 1

		cape_cin = cape_wrap(p_hpa, tk, qv, z, ter, psfc_hpa, missing, i3dflag, ter_follow, omp_threads)
		comp = cape_cin.compute(num_workers)
		
		return ma.masked_values(comp, missing)
		
	def get_dbz(daskArray, use_varint=False, use_liqskin=False, omp_threads=1, num_workers=1):
		t = daskArray["T"]
		p = daskArray["P"]
		pb = daskArray["PB"]
		qv = daskArray["QVAPOR"]
		qr = daskArray["QRAIN"]	
		
		try:
			qs = daskArray["QSNOW"]
		except KeyError:
			qs_np = np.zeros(qv.shape, qv.dtype)
			qs = da_from_array(qs_np)
			
		try:
			qgraup = daskArray["QGRAUP"]
		except KeyError:
			qgraup_np = np.zeros(qv.shape, qv.dtype)
			qgraup = da_from_array(qgraup_np)	

		full_t = map_blocks(wrapped_add, Constants.T_BASE, t, omp_threads, dtype=t.dtype)
		full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
		tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

		sn0 = 1 if qs.any() else 0
		ivarint = 1 if use_varint else 0
		iliqskin = 1 if use_liqskin else 0		
		
		dbz = map_blocks(dbz_wrap, full_p, tk, qv, qr, qs, qg, sn0, ivarint, iliqskin, omp_threads, dtype=p.dtype)
		return dbz.compute(num_workers)		