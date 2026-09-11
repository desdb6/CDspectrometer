"""
Script to compare helicoid 225 data.
Author: Des De Borger
Last modified: 09/09/2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

desktop_data = np.genfromtxt(r"Outputs\20260910\225_Helicoids_dilution\1x\1x.csv", skip_header=1, delimiter=",")
desktop_wavelength = desktop_data[:, 1]
desktop_CD = desktop_data[:, 9]
desktop_g = desktop_data[:, 10]
desktop_weak_mask = np.genfromtxt(
        r"Outputs\20260910\225_Helicoids_dilution\1x\1x.csv",
        skip_header=1, delimiter=",",
        usecols=12, dtype=str
    ) == "True"
desktop_abs = desktop_data[:, 11]

hq_data = np.genfromtxt(r"Outputs\20260910\225_Helicoids\225_huuquang.csv", skip_header=1, delimiter=",")
hq_wavelength = hq_data[:, 0]
hq_CD = hq_data[:, 2]
hq_g = hq_data[:, 1]
hq_abs = hq_data[:, 3]

CD_data = np.genfromtxt(r"Outputs\20260910\225_Helicoids\225_CD.txt", skip_header=1)
CD_wavelength = CD_data[:, 0]
CD_CD = CD_data[:, 2]
CD_g = CD_data[:, 1]
CD_abs = CD_data[:, 3]

# --- Plot 1: CD spectra ---

plt.figure()
plt.plot(desktop_wavelength, desktop_CD, label="Desktop CD")
plt.plot(hq_wavelength, hq_CD, label="Provided data")
plt.plot(CD_wavelength, CD_CD, label="CD")
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    desktop_wavelength, 0, 1,
    where=desktop_weak_mask,
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("CD (mdeg)")
plt.title("Helicoid 225 - CD comparison")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

# --- Plot 2: g-factor spectra ---

plt.figure()
plt.plot(desktop_wavelength, desktop_g, label="Desktop CD")
plt.plot(hq_wavelength, hq_g, label="Provided data")
plt.plot(CD_wavelength, CD_g, label="CD")
trans2 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    desktop_wavelength, 0, 1,
    where=desktop_weak_mask,
    color="#777777", alpha=0.5,
    transform=trans2,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("g-factor")
plt.ylim([-0.2, 0.2])
plt.title("Helicoid 225 - g-factor comparison")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

# --- Plot 3: Absorbance spectra ---

plt.figure()
plt.plot(desktop_wavelength, desktop_abs, label="Desktop CD")
plt.plot(hq_wavelength, hq_abs, label="Provided data")
plt.plot(CD_wavelength, CD_abs, label="CD")
trans3 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    desktop_wavelength, 0, 1,
    where=desktop_weak_mask,
    color="#777777", alpha=0.5,
    transform=trans3,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("Absorbance")
plt.title("Helicoid 225 - Absorbance comparison")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

plt.show()