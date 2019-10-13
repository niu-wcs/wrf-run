#!/usr/bin/python
# Calculation.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This class instance handles the parallel calculation routines for dask
#  - Notes on how this implementation is handled is shown here:
#     https://github.com/NCAR/wrf-python/wiki/How-to-add-dask-support

import numpy as np
import xarray
import dask.array as da
import dask.array.ma as ma
import numpy.ma as npma
from dask.array import map_blocks
from wrf import Constants, ConversionFactors
from wrf.constants import default_fill
from ArrayTools import wrapped_destagger, wrapped_either, wrapped_lat_varname, wrapped_lon_varname, wrapped_interplevel, fetch_variable
import PyPostTools
		
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

def eth_wrap(qv, tk, full_p, omp_threads=1):
	from wrf.extension import _eth, omp_set_num_threads

	omp_set_num_threads(omp_threads)
	result = _eth(qv, tk, full_p)

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
def get_full_p(daskArray):
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	
	total_p = map_blocks(wrapped_add, p, pb, dtype=p.dtype)
	full_p = map_blocks(wrapped_div, total_p, 100, dtype=p.dtype)

	return full_p

def get_winds_at_level(daskArray, vertical_field=None, requested_top=0., omp_threads=1):
    varname = wrapped_either(daskArray, ("U", "UU"))
    uS = fetch_variable(daskArray, varname)
    u = wrapped_destagger(uS, -1)
    
    varname = wrapped_either(daskArray, ("V", "VV"))
    vS = fetch_variable(daskArray, varname)
    v = wrapped_destagger(vS, -2)

    del(varname)
    del(uS)
    del(vS)

    if(requested_top == 0.):
        return u[0], v[0]
    else:
        uLev = wrapped_interplevel(u, vertical_field, requested_top, omp_threads=omp_threads)
        vLev = wrapped_interplevel(v, vertical_field, requested_top, omp_threads=omp_threads)
        return uLev, vLev

def get_wind_shear(daskArray, top=6000.0, omp_threads=1, z=None):
	if(len(z) == 0):
		z = get_height(daskArray, omp_threads=omp_threads)

	u0, v0 = get_winds_at_level(daskArray, omp_threads=omp_threads)
	ut, vt = get_winds_at_level(daskArray, z, top, omp_threads=omp_threads)

	uS = map_blocks(wrapped_sub, ut, u0, dtype=u0.dtype) #ut - u0
	vS = map_blocks(wrapped_sub, vt, v0, dtype=v0.dtype) #vt - v0   

	speed = da.sqrt(uS*uS + vS*vS)

	del(z)
	del(u0)
	del(v0)
	del(ut)
	del(vt)

	uComp = uS
	vComp = vS
	sComp = speed

	return uComp, vComp, sComp

def get_theta(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, omp_threads, dtype=t.dtype)
	
	return full_t

def get_tk(daskArray, omp_threads):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	dtype = t.dtype
	
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)	
	
	del(t)
	del(p)
	del(pb)
	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	return tk

def get_tv(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qv = fetch_variable(daskArray, "QVAPOR")
	dtype = t.dtype

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	
	del(t)
	del(p)
	del(pb)
	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	tv = map_blocks(tv_wrap, tk, qv, omp_threads, dtype=dtype)
	return tv
	
def get_eth(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qv = fetch_variable(daskArray, "QVAPOR")
	dtype = t.dtype

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)

	del(t)
	del(p)
	del(pb)

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	del(full_t)

	eth = map_blocks(eth_wrap, qv, tk, full_p, omp_threads, dtype=dtype)
	return eth
	
def get_tw(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qv = fetch_variable(daskArray, "QVAPOR")
	dtype = t.dtype
	
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)	
	
	del(t)
	del(p)
	del(pb)
	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	tw = map_blocks(wetbulb_wrap, tk, qv, omp_threads, dtype=dtype)
	return tw
	
def get_cape3d(daskArray, omp_threads=1):	
    missing = default_fill(np.float64)

    t = fetch_variable(daskArray, "T")
    p = fetch_variable(daskArray, "P")
    pb = fetch_variable(daskArray, "PB")
    qv = fetch_variable(daskArray, "QVAPOR")
    ph = fetch_variable(daskArray, "PH")
    phb = fetch_variable(daskArray, "PHB")
    ter = fetch_variable(daskArray, "HGT")
    psfc = fetch_variable(daskArray, "PSFC")
    dtype = p.dtype

    full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
    full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
    tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)

    del(full_t)
    del(t)
    del(p)

    geopt = map_blocks(wrapped_add, ph, phb, dtype=dtype)
    geopt_unstag = wrapped_destagger(geopt, -3)
    z = map_blocks(wrapped_div, geopt_unstag, Constants.G, dtype=dtype)

    del(ph)
    del(phb)
    del(geopt)
    del(geopt_unstag)

    p_hpa = map_blocks(wrapped_mul, full_p, ConversionFactors.PA_TO_HPA, dtype=dtype)
    psfc_hpa = map_blocks(wrapped_mul, psfc, ConversionFactors.PA_TO_HPA, dtype=dtype)

    del(full_p)
    del(psfc)

    i3dflag = 1
    ter_follow = 1

    cape_cin = map_blocks(cape_wrap, p_hpa, tk, qv, z, ter, psfc_hpa, missing, i3dflag, ter_follow, omp_threads, dtype=dtype)
    return cape_cin
	
# RF: TO-DO find a way to remove the compute() call inside the function, then remove num_workers from parm list.
def get_cape2d(daskArray, omp_threads=1, num_workers=1):	
	missing = default_fill(np.float64)

	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qv = fetch_variable(daskArray, "QVAPOR")
	ph = fetch_variable(daskArray, "PH")
	phb = fetch_variable(daskArray, "PHB")
	ter = fetch_variable(daskArray, "HGT")
	psfc = fetch_variable(daskArray, "PSFC")
	dtype = p.dtype

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)

	del(full_t)
	del(t)
	del(p)

	geopt = map_blocks(wrapped_add, ph, phb, dtype=dtype)
	geopt_unstag = wrapped_destagger(geopt, -3)
	z = map_blocks(wrapped_div, geopt_unstag, Constants.G, dtype=dtype)

	del(ph)
	del(phb)
	del(geopt)
	del(geopt_unstag)

	p_hpa = map_blocks(wrapped_mul, full_p, ConversionFactors.PA_TO_HPA, dtype=dtype)
	psfc_hpa = map_blocks(wrapped_mul, psfc, ConversionFactors.PA_TO_HPA, dtype=dtype)

	del(full_p)
	del(psfc)

	i3dflag = 0
	ter_follow = 1

	cape_cin = map_blocks(cape_wrap, p_hpa, tk, qv, z, ter, psfc_hpa, missing, i3dflag, ter_follow, omp_threads, dtype=dtype)
	calc_cape = cape_cin.compute(num_workers=num_workers)

	left_dims = calc_cape.shape[1:-3]
	right_dims = calc_cape.shape[-2:]

	resdim = (4,) + left_dims + right_dims

	# Make a new output array for the result
	result = np.zeros(resdim, calc_cape.dtype)

	# Cape 2D output is not flipped in the vertical, so index from the
	# end
	result[0, ..., :, :] = calc_cape[0, ..., -1, :, :]
	result[1, ..., :, :] = calc_cape[1, ..., -1, :, :]
	result[2, ..., :, :] = calc_cape[1, ..., -2, :, :]
	result[3, ..., :, :] = calc_cape[1, ..., -3, :, :]

	return npma.masked_values(result, missing)
	
def get_dbz(daskArray, use_varint=False, use_liqskin=False, omp_threads=1):
    t = fetch_variable(daskArray, "T")
    p = fetch_variable(daskArray, "P")
    pb = fetch_variable(daskArray, "PB")
    qv = fetch_variable(daskArray, "QVAPOR")
    qr = fetch_variable(daskArray, "QRAIN")

    dtype = t.dtype

    try:
        qs = fetch_variable(daskArray, "QSNOW")
    except KeyError:
        qs = da.zeros(qv.shape, qv.dtype)

    try:
        qgraup = fetch_variable(daskArray, "QGRAUP")
    except KeyError:
        qgraup = da.zeros(qv.shape, qv.dtype)

    full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=t.dtype)
    full_p = map_blocks(wrapped_add, p, pb, dtype=p.dtype)
    tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=p.dtype)

    sn0 = 1 if qs.any() else 0
    ivarint = 1 if use_varint else 0
    iliqskin = 1 if use_liqskin else 0

    del(t)
    del(p)
    del(pb)

    dbz = map_blocks(dbz_wrap, full_p, tk, qv, qr, qs, qgraup, sn0, ivarint, iliqskin, omp_threads, dtype=dtype)
    return dbz

def get_dewpoint(daskArray, omp_threads=1):
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qvapor = fetch_variable(daskArray, "QVAPOR", include_meta=True)
	dtype = p.dtype
	
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	full_p_div = map_blocks(wrapped_mul, full_p, 0.01, dtype=dtype)
	
	del(p)
	del(pb)
	del(full_p)
	
	qvapor = qvapor.where(qvapor >= 0, 0)
	
	td = map_blocks(td_wrap, full_p_div, qvapor.data, omp_threads, dtype=dtype)
	return td
	
def get_geoht(daskArray, height=True, msl=True, omp_threads=1):
	varname = wrapped_either(daskArray, ("PH", "GHT"))
	if varname == "PH":
		ph = fetch_variable(daskArray, "PH")
		phb = fetch_variable(daskArray, "PHB")
		hgt = fetch_variable(daskArray, "HGT")
		dtype = ph.dtype
		geopt = map_blocks(wrapped_add, ph, phb, dtype=dtype)
		geopt_f = wrapped_destagger(geopt, -3)
	else:
		geopt = fetch_variable(daskArray, "GHT")
		hgt = fetch_variable(daskArray, "HGT_M")
		dtype = geopt.dtype
		geopt_f = map_blocks(wrapped_mul, geopt, Constants.G, dtype=dtype)

	if height:
		if msl:
			mslh = map_blocks(wrapped_div, geopt_f, Constants.G, dtype=dtype)
			return mslh
		else:
			# Due to broadcasting with multifile/multitime, the 2D terrain
			# array needs to be reshaped to a 3D array so the right dims
			# line up
			new_dims = list(hgt.shape)
			new_dims.insert(-2, 1)
			hgt = hgt.reshape(new_dims)

			mslh = map_blocks(wrapped_div, geopt_f, Constants.G, dtype=dtype)
			mslh_f = map_blocks(wrapped_sub, mslh, hgt, dtype=dtype)
			return mslh_f
	else:
		return geopt_f

def get_height(daskArray, msl=True, omp_threads=1):
	return get_geoht(daskArray, height=True, msl=msl, omp_threads=omp_threads)
	
def get_height_agl(daskArray, omp_threads=1):
	return get_geoht(daskArray, height=True, msl=False, omp_threads=omp_threads)
	
def get_srh(daskArray, top=3000.0, omp_threads=1):
    lat_VN = wrapped_lat_varname(daskArray, stagger=None)
    lats = fetch_variable(daskArray, lat_VN)

    hgt = fetch_variable(daskArray, "HGT")
    ph = fetch_variable(daskArray, "PH")
    phb = fetch_variable(daskArray, "PHB")
    dtype = ph.dtype

    varname = wrapped_either(daskArray, ("U", "UU"))
    uS = fetch_variable(daskArray, varname)
    u = wrapped_destagger(uS, -1)

    varname = wrapped_either(daskArray, ("V", "VV"))
    vS = fetch_variable(daskArray, varname)
    v = wrapped_destagger(vS, -2)

    geopt = map_blocks(wrapped_add, ph, phb, dtype=dtype)
    geopt_f = wrapped_destagger(geopt, -3)
    z = map_blocks(wrapped_div, geopt_f, Constants.G, dtype=dtype)

    del(ph)
    del(phb)
    del(geopt)
    del(geopt_f)

    u1 = np.ascontiguousarray(u[..., ::-1, :, :])
    v1 = np.ascontiguousarray(v[..., ::-1, :, :])
    z1 = np.ascontiguousarray(z[..., ::-1, :, :])

    del(u)
    del(v)
    del(z)

    srh = map_blocks(srh_wrap, u1, v1, z1, hgt, lats, top, omp_threads, dtype=dtype)
    return srh
	
def get_udhel(daskArray, bottom=2000.0, top=5000.0, omp_threads=1):
    wstag = fetch_variable(daskArray, "W")
    ph = fetch_variable(daskArray, "PH")
    phb = fetch_variable(daskArray, "PHB")
    dtype = ph.dtype

    mapfct = fetch_variable(daskArray, "MAPFAC_M")
    dx = daskArray.DX
    dy = daskArray.DY

    varname = wrapped_either(daskArray, ("U", "UU"))
    uS = fetch_variable(daskArray, varname)
    u = wrapped_destagger(uS, -1)

    varname = wrapped_either(daskArray, ("V", "VV"))
    vS = fetch_variable(daskArray, varname)
    v = wrapped_destagger(vS, -2)

    del(uS)
    del(vS)

    geopt = map_blocks(wrapped_add, ph, phb, dtype=dtype)
    zp = map_blocks(wrapped_div, geopt, Constants.G, dtype=dtype)

    del(ph)
    del(phb)
    del(geopt)

    udhel = map_blocks(udhel_wrap, zp, mapfct, u, v, wstag, dx, dy, bottom, top, omp_threads, dtype=dtype)
    return udhel
	
def get_omega(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	w = fetch_variable(daskArray, "W")
	pb = fetch_variable(daskArray, "PB")
	qv = fetch_variable(daskArray, "QVAPOR")
	
	dtype = t.dtype

	wa = wrapped_destagger(w, -3)
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)	
	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	
	del(t)
	del(p)
	del(pb)
	del(full_t)

	omega = map_blocks(omega_wrap, qv, tk, wa, full_p, omp_threads, dtype=dtype)
	return omega
	
def get_accum_precip(daskArray, omp_threads=1):
	rainc = fetch_variable(daskArray, "RAINC")
	rainnc = fetch_variable(daskArray, "RAINNC")	
	rainsum = map_blocks(wrapped_add, rainc, rainnc, dtype=rainc.dtype)
	return rainsum
	
def get_pw(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	ph = fetch_variable(daskArray, "PH")
	phb = fetch_variable(daskArray, "PHB")
	qv = fetch_variable(daskArray, "QVAPOR")
	
	dtype = t.dtype

	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	full_ph = map_blocks(wrapped_add, ph, phb, dtype=dtype)
	ht = map_blocks(wrapped_div, full_ph, Constants.G, dtype=dtype)
	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	
	del(p)
	del(pb)
	del(ph)

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	tv = map_blocks(tv_wrap, tk, qv, omp_threads, dtype=dtype)
	
	del(full_t)
	del(tk)

	pw = map_blocks(pw_wrap, full_p, tv, qv, ht, omp_threads, dtype=dtype)
	return pw
	
def get_rh(daskArray, omp_threads=1):
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	qvapor = fetch_variable(daskArray, "QVAPOR", include_meta=True)
	dtype = t.dtype

	full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	
	del(t)
	del(p)
	del(pb)

	qvapor = qvapor.where(qvapor >= 0, 0)

	tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
	del(full_t)
	
	rh = map_blocks(rh_wrap, qvapor.data, full_p, tk, omp_threads, dtype=dtype)
	return rh
	
def get_slp(daskArray, omp_threads=1):
    t = fetch_variable(daskArray, "T")
    p = fetch_variable(daskArray, "P")
    pb = fetch_variable(daskArray, "PB")
    qvapor = fetch_variable(daskArray, "QVAPOR", include_meta=True)
    ph = fetch_variable(daskArray, "PH")
    phb = fetch_variable(daskArray, "PHB")
    dtype = p.dtype

    full_t = map_blocks(wrapped_add, t, Constants.T_BASE, dtype=dtype)
    full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
    qvapor = qvapor.where(qvapor >= 0, 0)

    del(t)
    del(p)
    del(pb)

    pre_full_ph = map_blocks(wrapped_add, ph, phb, dtype=dtype)
    full_ph = map_blocks(wrapped_div, pre_full_ph, Constants.G, dtype=dtype)
    destag_ph = wrapped_destagger(full_ph, -3) 

    del(full_ph)
    del(ph)
    del(phb)

    tk = map_blocks(tk_wrap, full_p, full_t, omp_threads, dtype=dtype)
    slp = map_blocks(slp_wrap, destag_ph, tk, full_p, qvapor.data, omp_threads, dtype=dtype)
    slp_calc = slp

    return slp_calc
	
def get_avo(daskArray, omp_threads=1):
	u = fetch_variable(daskArray, "U")
	v = fetch_variable(daskArray, "V")
	msfu = fetch_variable(daskArray, "MAPFAC_U")
	msfv = fetch_variable(daskArray, "MAPFAC_V")
	msfm = fetch_variable(daskArray, "MAPFAC_M")
	cor = fetch_variable(daskArray, "F")

	dx = daskArray.DX
	dy = daskArray.DY
	
	dtype = u.dtype

	avo = map_blocks(avo_wrap, u, v, msfu, msfv, msfm, cor, dx, dy, omp_threads, dtype=dtype)
	return avo
	
def get_rvor(daskArray, omp_threads=1):
	u = fetch_variable(daskArray, "U")
	v = fetch_variable(daskArray, "V")
	msfu = fetch_variable(daskArray, "MAPFAC_U")
	msfv = fetch_variable(daskArray, "MAPFAC_V")
	msfm = fetch_variable(daskArray, "MAPFAC_M")
	cor = fetch_variable(daskArray, "F")

	dx = daskArray.DX
	dy = daskArray.DY

	dtype = u.dtype

	avo = map_blocks(avo_wrap, u, v, msfu, msfv, msfm, cor, dx, dy, omp_threads, dtype=dtype)
	rvor = map_blocks(wrapped_sub, avo, cor, dtype=dtype)

	return rvor
	
def get_pvo(daskArray, omp_threads=1):
	u = fetch_variable(daskArray, "U")
	v = fetch_variable(daskArray, "V")
	t = fetch_variable(daskArray, "T")
	p = fetch_variable(daskArray, "P")
	pb = fetch_variable(daskArray, "PB")
	msfu = fetch_variable(daskArray, "MAPFAC_U")
	msfv = fetch_variable(daskArray, "MAPFAC_V")
	msfm = fetch_variable(daskArray, "MAPFAC_M")
	cor = fetch_variable(daskArray, "F")

	dx = daskArray.DX
	dy = daskArray.DY
	
	dtype=u.dtype

	full_t = map_blocks(wrapped_add, t, 300, dtype=dtype)
	full_p = map_blocks(wrapped_add, p, pb, dtype=dtype)
	
	del(t)
	del(p)
	del(pb)

	pvo = map_blocks(pvo_wrap, u, v, full_t, full_p, msfu, msfv, msfm, cor, dx, dy, omp_threads, dtype=dtype)
	return pvo