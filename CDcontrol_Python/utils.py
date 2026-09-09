"""
Utils functions for absorbance and CD spectroscopy.
Author: Des De Borger
Last modified: 08/09/2026
"""

import numpy as np
import matplotlib.pyplot as plt

def absorbance(intensity_0: float, intensity: float):
    """Calculate absorbance"""
    return np.log10(intensity_0 / intensity)

def avg_absorbance(intensity_l: float, intensity_r: float, intensity_l0: float, intensity_r0: float):
    """Calculate the absorbance when measuring a CD signal by averaging the absorbance of the two handednesses"""
    return (absorbance(intensity_l0, intensity_l) + absorbance(intensity_r0, intensity_r)) / 2

def delta_absorbance(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as absorbance difference"""
    return np.log10(intensity_r / intensity_l)

def ellipticity_deg(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as ellipticity"""
    return delta_absorbance(intensity_r, intensity_l) * np.log(10) * 45 / np.pi

def ellipticity_millideg(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as ellipticity in millidegrees"""
    return 1000 * ellipticity_deg(intensity_r, intensity_l)

def g_factor(intensity_l: float, intensity_r: float, intensity_l0: float, intensity_r0: float):
    """Calculate the g-factor"""
    return (delta_absorbance(intensity_l, intensity_r) - delta_absorbance(intensity_l0, intensity_r0)) / avg_absorbance(intensity_l, intensity_r, intensity_l0, intensity_r0)
