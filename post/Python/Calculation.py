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
from wrf.utils import either
from wrf.latlonutils import _lat_varname, _lon_varname
from ArrayTools import wrapped_unstagger, to_np, to_da
		
"""
	This block contains simple wrappers for basic mathematical operations, this is needed to support
	 basic calculation routines that are not thread-safe in the wrf-python library so dask can
	 properly handle these in large scale computing environments
"""
# Wrapped call for simple addition
def wrapped_add(base, add):
	return base + add	
	
# Wrapped call for simple subtraction
def wrapped_sub(base, sub):
	return base - sub
	
# Wrapped call for simple multiplication
def wrapped_mul(base, prod):
	return base * prod

# Wrapped call for simple division
def wrapped_div(base, div):
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
	# NOTE: _wetbulb is potentially not thread-safe, this may require a re-write at some point, but just to be aware.
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
	# NOTE: _cape is potentially not thread-safe, this may require a re-write at some point, but just to be aware.
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
	This block of code handles the multiprocessed variable calculation routines.
	 -> These are wrapped calls of the original g_func* methods in the wrf-python library
"""
def get_theta(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	
	return full_t.compute(num_workers)

def get_tk(daskArray, omp_threads, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	return tk.compute(num_workers)

def get_tv(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	qv = daskArray["QVAPOR"]	

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	tv = map_blocks(tv_wrap, tk, qv, omp_threads, dtype=p.dtype)
	return tv.compute(num_workers)	
	
def get_tw(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	qv = daskArray["QVAPOR"]
	
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	tw = map_blocks(wetbulb_wrap, tk, qv, omp_threads, dtype=p.dtype)
	return tw.compute(num_workers)
	
def get_cape3d(daskArray, omp_threads=1, num_workers=1):	
	missing = default_fill(np.float64)
	
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	qv = daskArray["QVAPOR"]
	ph = daskArray["PH"]
	phb = daskArray["PHB"]
	ter = daskArray["HGT"]
	psfc = daskArray["PSFC"]

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

	geopt = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
	geopt_unstag = wrapped_unstagger(geopt, -3, num_workers)
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
		qs = da.from_array(qs_np)
		
	try:
		qgraup = daskArray["QGRAUP"]
	except KeyError:
		qgraup_np = np.zeros(qv.shape, qv.dtype)
		qgraup = da.from_array(qgraup_np)	

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

	sn0 = 1 if qs.any() else 0
	ivarint = 1 if use_varint else 0
	iliqskin = 1 if use_liqskin else 0		
	
	dbz = map_blocks(dbz_wrap, full_p, tk, qv, qr, qs, qg, sn0, ivarint, iliqskin, omp_threads, dtype=p.dtype)
	return dbz.compute(num_workers)	

def get_dewpoint(daskArray, omp_threads=1, num_workers=1):
	p = daskArray["P"]
	pb = daskArray["PB"]
	qvapor = daskArray["QVAPOR"].copy()		
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)
	full_p_div = map_blocks(wrapped_mul, full_p, 0.01, omp_threads, dtype=p.dtype)
	qvapor[qvapor < 0] = 0.
	
	td = map_blocks(td_wrap, full_p_div, qvapor, omp_threads, dtype=p.dtype)
	return td.compute(num_workers)
	
def get_geoht(daskArray, height=True, msl=True, omp_threads=1, num_workers=1):
	varname = either("PH", "GHT")(daskArray)
	if varname == "PH":
		ph = daskArray["PH"]
		phb = daskArray["PHB"]
		hgt = daskArray["HGT"]
		geopt = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
		geopt_f = wrapped_unstagger(geopt, -3, num_workers)
	else:
		geopt = daskArray["GHT"]
		hgt = daskArray["HGT_M"]
		geopt_f = map_blocks(wrapped_mul, geopt, Constants.G, omp_threads, dtype=ph.dtype)

	if height:
		if msl:
			mslh = map_blocks(wrapped_div, geopt_f, Constants.G, omp_threads, dtype=ph.dtype)
			return mslh.compute(num_workers)
		else:
			# Due to broadcasting with multifile/multitime, the 2D terrain
			# array needs to be reshaped to a 3D array so the right dims
			# line up
			new_dims = list(hgt.shape)
			new_dims.insert(-2, 1)
			hgt = hgt.reshape(new_dims)

			mslh = map_blocks(wrapped_div, geopt_f, Constants.G, omp_threads, dtype=ph.dtype)
			mslh_f = map_blocks(wrapped_sub, mslh, hgt, omp_threads, dtype=ph.dtype)
			return mslh_f.compute(num_workers)
	else:
		return geopt_f.compute(num_workers)	

def get_height(daskArray, msl=True, omp_threads=1, num_workers=1):
	return get_geoht(daskArray, height=True, msl=msl, omp_threads=omp_threads, num_workers=num_workers)
	
def get_height_agl(daskArray, omp_threads=1, num_workers=1):
	return get_geoht(daskArray, height=True, msl=False, omp_threads=omp_threads, num_workers=num_workers)
	
def get_srh(daskArray, top=3000.0, omp_threads=1, num_workers=1):
	lat_VN = _lat_varname(wrfin, stagger=None)
	lats = daskArray[lat_VN]

	hgt = daskArray["HGT"]
	ph = daskArray["PH"]
	phb = daskArray["PHB"]

	varname = either("U", "UU")(daskArray)
	uS = daskArray[varname]
	u = wrapped_unstagger(daskArray[varname], -1, num_workers, save_numpy=True)

	varname = either("V", "VV")(daskArray)
	vS = daskArray[varname]
	v = wrapped_unstagger(daskArray[varname], -2, num_workers, save_numpy=True)

	geopt = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
	geopt_f = wrapped_unstagger(geopt, -3, num_workers)	
	zS = map_blocks(wrapped_div, geopt_f, Constants.G, omp_threads, dtype=ph.dtype)
	z = to_np(zS, num_workers)

	u1 = to_da(np.ascontiguousarray(u[..., ::-1, :, :]))
	v1 = to_da(np.ascontiguousarray(v[..., ::-1, :, :]))
	z1 = to_da(np.ascontiguousarray(z[..., ::-1, :, :]))

	srh = srh_wrap(u1, v1, z1, hgt, lats, top, omp_threads)
	return srh.compute(num_workers)
	
def get_udhel(daskArray, bottom=2000.0, top=5000.0, omp_threads=1, num_workers=1):
	wstag = daskArray["W"]
	ph = daskArray["PH"]
	phb = daskArray["PHB"]
	mapfct = daskArray["MAPFAC_M"]

	dx = daskArray["DX"]
	dy = daskArray["DY"]

	varname = either("U", "UU")(daskArray)
	uS = daskArray[varname]
	u = wrapped_unstagger(daskArray[varname], -1, num_workers)

	varname = either("V", "VV")(daskArray)
	vS = daskArray[varname]
	v = wrapped_unstagger(daskArray[varname], -2, num_workers)	

	geopt = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
	geopt_f = wrapped_unstagger(geopt, -3, num_workers)	
	zp = map_blocks(wrapped_div, geopt_f, Constants.G, omp_threads, dtype=ph.dtype)	

	udhel = udhel_wrap(zp, mapfct, u, v, wstag, dx, dy, bottom, top, omp_threads)
	return udhel.compute(num_workers)
	
def get_omega(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	w = daskArray["W"]
	pb = daskArray["PB"]
	qv = daskArray["QVAPOR"]

	wa = wrapped_unstagger(w, -3, num_workers)
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

	omega = omega_wrap(qv, tk, wa, full_p, omp_threads)
	return omega.compute(num_workers)
	
def get_accum_precip(daskArray, omp_threads=1, num_workers=1):
	rainc = daskArray["RAINC"]
	rainnc = daskArray["RAINNC"]	
	rainsum = map_blocks(wrapped_add, rainc, rainnc, omp_threads, dtype=rainc.dtype)
	return rainsum.compute(num_workers)
	
def get_pw(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	ph = daskArray["PH"]
	phb = daskArray["PHB"]
	qv = daskArray["QVAPOR"]

	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)
	full_ph = map_blocks(wrapped_add, ph, pb, omp_threads, dtype=ph.dtype)
	ht = map_blocks(wrapped_div, full_ph, Constants.G, omp_threads, dtype=p.dtype)
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	tv = map_blocks(tv_wrap, tk, qv, omp_threads, dtype=p.dtype)

	pw = pw_wrap(full_p, tv, qv, ht, omp_threads)
	return pw.compute(num_workers)
	
def get_rh(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	qvapor = daskArray["QVAPOR"].copy()

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)

	qvapor[qvapor < 0] = 0.

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	rh = map_blocks(rh_wrap, qvapor, full_p, tk, omp_threads, dtype=p.dtype)
	
def get_slp(daskArray, omp_threads=1, num_workers=1):
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	qvapor = daskArray["QVAPOR"].copy()
	ph = daskArray["PH"]
	phb = daskArray["PHB"]	

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)
	qvapor[qvapor < 0] = 0.	

	pre_full_ph = map_blocks(wrapped_add, ph, phb, omp_threads, dtype=ph.dtype)
	full_ph = map_blocks(wrapped_div, pre_full_ph, Constants.G, omp_threads, dtype=ph.dtype)
	destag_ph = wrapped_unstagger(full_ph, -3, num_workers)

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)
	slp = slp_wrap(destag_ph, tk, full_p, qvapor, omp_threads)
	return slp.compute(num_workers)
	
def get_avo(daskArray, omp_threads=1, num_workers=1):
	u = daskArray["U"]
	v = daskArray["V"]
	msfu = daskArray["MAPFAC_U"]
	msfv = daskArray["MAPFAC_V"]
	msfm = daskArray["MAPFAC_M"]
	cor = daskArray["F"]

	dx = daskArray["DX"]
	dy = daskArray["DY"]

	avo = avo_wrap(u, v, msfu, msfv, msfm, cor, dx, dy, omp_threads)
	return avo.compute(num_workers)
	
def get_rvor(daskArray, omp_threads=1, num_workers=1):
	u = daskArray["U"]
	v = daskArray["V"]
	msfu = daskArray["MAPFAC_U"]
	msfv = daskArray["MAPFAC_V"]
	msfm = daskArray["MAPFAC_M"]
	cor = daskArray["F"]

	dx = daskArray["DX"]
	dy = daskArray["DY"]

	avo = avo_wrap(u, v, msfu, msfv, msfm, cor, dx, dy, omp_threads)
	rvor = map_blocks(wrapped_sub, avo, cor, omp_threads, dtype=cor.dtype)

	return rvor.compute(num_workers)
	
def get_pvo(daskArray, omp_threads=1, num_workers=1):
	u = daskArray["U"]
	v = daskArray["V"]
	t = daskArray["T"]
	p = daskArray["P"]
	pb = daskArray["PB"]
	msfu = daskArray["MAPFAC_U"]
	msfv = daskArray["MAPFAC_V"]
	msfm = daskArray["MAPFAC_M"]
	cor = daskArray["F"]

	dx = daskArray["DX"]
	dy = daskArray["DY"]

	full_t = map_blocks(wrapped_add, t, 300, omp_threads, dtype=t.dtype)
	full_p = map_blocks(wrapped_add, p, pb, omp_threads, dtype=p.dtype)

	pvo = pvo_wrap(u, v, full_t, full_p, msfu, msfv, msfm, cor, dx, dy, omp_threads)
	return pvo.compute(num_workers)