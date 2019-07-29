#!/usr/bin/python
# Conversions.py
# Robert C Fritzen - Dpt. Geographic & Atmospheric Sciences
#
# This file defines unit conversion methods

import numpy as np
import xarray

"""
	Important Constants
"""
G_CONSTANT = 9.81

# K_to_C(): Convert Temperature in Kelvin to Celsius
def K_to_C(X):
	return X - 273.15
	
# C_to_F(): Convert Temperature in Celsius to Fahrenheit
def C_to_F(X):
	return (X * (9./5.)) + 32.

# K_to_F(): Convert Temperature in Kelvin to Fahrenheit
def K_to_F(X):
	return C_to_F(K_to_C(X))

# pa_to_mb(X): Convert Pascals to Milibars / Hectapascals
def pa_to_mb(X):
	return X * 0.01
	
# mm_to_in(): Convert milimeters to inches
def mm_to_in(X):
	return X * 0.0393701
	
# ms_to_kts(): Convert meters per second to knots
def ms_to_kts(X):
	return X * 1.94384449
	
# Convert PW units of kg m^-2 to inches
def kgm2_to_in(X):
	return X * 0.0393701