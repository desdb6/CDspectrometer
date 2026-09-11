"""
Script to compare dilution helicoid 225 data.
Author: Des De Borger
Last modified: 10/09/2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

from utils import *

data_100x = get_data_from_txt_abs(r"Outputs\Des\20260911\Nanosphere_dilution\100x.csv")
data_500x = get_data_from_txt_abs(r"Outputs\Des\20260911\Nanosphere_dilution\500x.csv")

data_ref = np.genfromtxt(r"Outputs\Des\20260911\Nanosphere_dilution\Des Abs.csv", skip_header=2, delimiter=",")
data_ref_500x_wl = data_ref[:, 0]
data_ref_500x_abs = data_ref[:, 3]
data_ref_100x_wl = data_ref[:, 8]
data_ref_100x_abs = data_ref[:, 9]

data_100x_concentration = au0_concentration(data_100x["Wavelength"], data_100x["Absorbance"])
data_500x_concentration = au0_concentration(data_500x["Wavelength"], data_500x["Absorbance"])


# --- Plot 1: 100x-factor ---

plt.figure()
plt.plot(data_100x["Wavelength"], data_100x["Absorbance"], label=f"1x, {data_100x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_ref_100x_wl, data_ref_100x_abs, label="Reference", alpha=0.8, linewidth=1)
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    data_100x["Wavelength"], 0, 1,
    where=data_100x["Weak signal mask"],
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("Absorbance")
plt.ylim([0, 0.1])
plt.xlim([400, 850])
plt.title("Nanosphere 100x dilution absorbance spectra")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

# --- Plot 1: 500x-factor ---

plt.figure()
plt.plot(data_500x["Wavelength"], data_500x["Absorbance"], label=f"1x, {data_500x_concentration:.4f} mM", alpha=0.8, linewidth=1)
plt.plot(data_ref_500x_wl, data_ref_500x_abs, label="Reference", alpha=0.8, linewidth=1)
trans1 = transforms.blended_transform_factory(plt.gca().transData, plt.gca().transAxes)
plt.fill_between(
    data_500x["Wavelength"], 0, 1,
    where=data_500x["Weak signal mask"],
    color="#777777", alpha=0.5,
    transform=trans1,
    )
plt.xlabel("Wavelength (nm)")
plt.ylabel("Absorbance")
plt.ylim([0, 0.025])
plt.xlim([400, 850])
plt.title("Nanosphere 500x dilution absorbance spectra")
plt.grid(alpha=0.4)
plt.legend()
plt.tight_layout()

plt.show()
