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
WAVELENGTHS_NM = np.arange(200.0, 3001.0, 1.0)
WAVELENGTHS_M = WAVELENGTHS_NM * 1e-9

def blackbody_dimless(T: float):
    x = (PLANCK * LIGHTSPEED) / (
        BOLTZMANN * T * WAVELENGTHS_M
    )

    blackbody = (WAVELENGTHS_M ** -5) / np.expm1(x)

    return blackbody / np.max(blackbody)

def rotation_matrix(theta: float):
    return np.array([
        [1, 0, 0, 0],
        [0, np.cos(2 * theta), np.sin(2 * theta), 0],
        [0, -np.sin(2 * theta), np.cos(2 * theta), 0],
        [0, 0, 0, 1]])

def lin_pol_matrix_theta0(k1: float, k2: float):
    return 1/2 * np.array([
        [k1 + k2, k1 - k2, 0, 0],
        [k1 - k2, k1 + k2, 0, 0],
        [0, 0, 2 * np.sqrt(k1 * k2), 0],
        [0, 0, 0, 2 * np.sqrt(k1 * k2)]
        ])

def lin_pol_matrix(theta: float, k1: float, k2: float):
    return np.matmul(np.matmul(rotation_matrix(-theta), lin_pol_matrix_theta0(k1, k2)), rotation_matrix(theta))

def lin_retarder_matrix(theta: float, delta: float):
    c2 = np.cos(2 * theta)
    s2 = np.sin(2 * theta)
    cd = np.cos(delta)
    sd = np.sin(delta)

    return np.array([
        [1, 0, 0, 0],
        [0, c2**2 + s2**2 * cd,       c2 * s2 * (1 - cd),   s2 * sd],
        [0, c2 * s2 * (1 - cd),       c2**2 * cd + s2**2,  -c2 * sd],
        [0, -s2 * sd,                 c2 * sd,               cd]
    ])

def load_lin_pol_interpolators(filepath: str):
    """
    Loads the wavelength-dependent Parallel/Perpendicular intensity data
    and returns two functions that linearly interpolate at any wavelength (in nm).
    """
    data = np.genfromtxt(filepath, delimiter=';', skip_header=1)
    wl, parallel, perpendicular = data[:, 0], data[:, 1], data[:, 2]

    def interp_parallel(wavelength_nm):
        return np.interp(wavelength_nm, wl, parallel)

    def interp_perpendicular(wavelength_nm):
        return np.interp(wavelength_nm, wl, perpendicular)

    return interp_parallel, interp_perpendicular

def load_retardance_interpolator(filepath: str):
    """
    Loads wavelength-dependent retardance (in waves) and returns a function
    that linearly interpolates at any wavelength (in nm).
    """
    data = np.genfromtxt(filepath, delimiter=';', skip_header=1)
    wl, retardance = data[:, 0], data[:, 1]

    def interp_retardance(wavelength_nm):
        return np.interp(wavelength_nm, wl, retardance)

    return interp_retardance

if __name__ == "__main__":
    interp_parallel, interp_perpendicular = load_lin_pol_interpolators(r"Spectral_Composition\lin_pol_data.csv")
    interp_retardance = load_retardance_interpolator(r"Spectral_Composition\fresnel_rhomb_data.csv")

    start_vector = np.array([1, 0, 0, 0])

    T = 2800 
    intensities = blackbody_dimless(T)

    stokes_vectors = np.zeros((len(WAVELENGTHS_NM), 4))
    stokes_vectors_scaled = np.zeros((len(WAVELENGTHS_NM), 4))

    for i, wl_nm in enumerate(WAVELENGTHS_NM):
        k1 = interp_parallel(wl_nm) / 100
        k2 = interp_perpendicular(wl_nm) / 100
        delta = interp_retardance(wl_nm) * 2 * np.pi

        operator_matrix = np.matmul(
            lin_retarder_matrix(0, delta),
            lin_pol_matrix(-np.pi / 4 , k1, k2)
        )
        end_vector = np.matmul(operator_matrix, start_vector)
        stokes_vectors[i] = end_vector
        stokes_vectors_scaled[i] = end_vector * intensities[i]

    # stokes_vectors[:, 0] is S0, [:, 1] is S1, [:, 2] is S2, [:, 3] is S3 (all vs wavelength)
    print(stokes_vectors[:, 3])
    plt.plot(WAVELENGTHS_NM, stokes_vectors[:, 3], label="S3 (circular)")
    plt.plot(WAVELENGTHS_NM, stokes_vectors[:, 0], label="S0 (intensity)")
    plt.plot(WAVELENGTHS_NM, stokes_vectors[:, 3]/stokes_vectors[:, 0], label="Circular fraction")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Stokes parameter")
    plt.legend()
    plt.grid()
    plt.show()