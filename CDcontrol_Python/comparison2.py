"""
Script to compare dilution helicoid 225 data.
Author: Des De Borger
Last modified: 10/09/2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

from utils import *

data_1x = get_data_from_txt(r"Outputs\Des\20260910\225_Helicoids_dilution\1x\1x.csv")
data_5x = get_data_from_txt(r"Outputs\Des\20260910\225_Helicoids_dilution\5x\5x.csv")
data_25x = get_data_from_txt(r"Outputs\Des\20260910\225_Helicoids_dilution\25xbis\25xbis.csv")
data_125x = get_data_from_txt(r"Outputs\Des\20260910\225_Helicoids_dilution\125x\125x.csv")

data_1x_concentration = au0_concentration(data_1x["Wavelength"], data_1x["Absorbance"])
data_5x_concentration = au0_concentration(data_5x["Wavelength"], data_5x["Absorbance"])
data_25x_concentration = au0_concentration(data_25x["Wavelength"], data_25x["Absorbance"])
data_125x_concentration = au0_concentration(data_125x["Wavelength"], data_125x["Absorbance"])

# --- Plot 1: g-factor ---

plt.figure()
plt.plot(data_1x["Wavelength"], data_1x["g-factor"], label=f"1x, {data_1x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_5x["Wavelength"], data_5x["g-factor"], label=f"5x, {data_5x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_25x["Wavelength"], data_25x["g-factor"], label=f"25x, {data_25x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_125x["Wavelength"], data_125x["g-factor"], label=f"125x, {data_125x_concentration:.4f} mM", alpha=0.8, linewidth=1)
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    data_1x["Wavelength"], 0, 1,
    where=data_1x["Weak signal mask"],
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("g-factor")
plt.ylim([-0.3, 0.3])
plt.xlim([400, 850])
plt.title("Helicoid 225 - g-factor comparison for diluted samples")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

# --- Plot 2: CD spectra ---

plt.figure()
plt.plot(data_1x["Wavelength"], data_1x["CD"], label=f"1x, {data_1x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_5x["Wavelength"], data_5x["CD"], label=f"5x, {data_5x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_25x["Wavelength"], data_25x["CD"], label=f"25x, {data_25x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_125x["Wavelength"], data_125x["CD"], label=f"125x, {data_125x_concentration:.4f} mM", alpha=0.8, linewidth=1)
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    data_1x["Wavelength"], 0, 1,
    where=data_1x["Weak signal mask"],
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("CD (mdeg)")
plt.ylim([-2000, 2000])
plt.xlim([400, 850])
plt.title("Helicoid 225 - CD comparison for diluted samples")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

# --- Plot 3: absorbance ---

plt.figure()
plt.plot(data_1x["Wavelength"], data_1x["Absorbance"], label=f"1x, {data_1x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_5x["Wavelength"], data_5x["Absorbance"], label=f"5x, {data_5x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_25x["Wavelength"], data_25x["Absorbance"], label=f"25x, {data_25x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_125x["Wavelength"], data_125x["Absorbance"], label=f"125x, {data_125x_concentration:.4f} mM", alpha=0.8, linewidth=1)
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    data_1x["Wavelength"], 0, 1,
    where=data_1x["Weak signal mask"],
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("Absorbance")
plt.ylim([0, 1])
plt.xlim([400, 850])
plt.title("Helicoid 225 - Absorbance for diluted samples")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

plt.show()
