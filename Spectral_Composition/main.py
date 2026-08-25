"""
Script to predict spectral composition of CPL beam
Author: Des De Borger
Last modified: 08/25/2026
"""

import numpy as np
import matplotlib.pyplot as plt

LIGHTSPEED = 3 * 10 ** 8
PLANCK = 6.626 * 10 ** -34
BOLTZMANN = 1.38 * 10 ** -23
WAVELENGTHS = np.arange(200.0, 3001.0, 1.0)  * 1e-9

def blackbody_dimless(T : float):
    blackbody = (WAVELENGTHS ** -5) * (np.exp((PLANCK * LIGHTSPEED)/(BOLTZMANN * T * WAVELENGTHS)) - 1) ** -1
    return blackbody / np.max(blackbody)

def lin_pol_mueller_matrix(k1: float, k2: float, theta: float):
    A = k1 + k2
    B = 2 * np.sqrt(k1*k2)
    matrix = np.array([
        [k1+ k2, (k1-k2) * np.cos(2 * theta), (k1-k2) * np.sin(2 * theta), 0],
        [(k1-k2) * np.cos(2 * theta), A * np.cos(2 * theta) ** 2 + B * np.sin(2 * theta) ** 2, (A - B) * np.sin(2 * theta) * np.cos(2 * theta), 0],
        [(k1-k2) * np.sin(2 * theta), (A - B) * np.sin(2 * theta) * np.cos(2 * theta), A * np.sin(2 * theta) ** 2 + B * np.cos(2 * theta) ** 2, 0],
        [0, 0, 0, B]
        ])
    return matrix / 2

if __name__ == "__main__":
    print(lin_pol_mueller_matrix(1, 0, np.pi/2))