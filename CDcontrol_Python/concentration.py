"""
Script to compare dilution helicoid 225 data.
Author: Des De Borger
Last modified: 10/09/2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms

from utils import *

data_1x = get_data_from_txt_abs(r"Outputs\Des\20260910\Nanodots_dilution\1x.csv")
data_10x = get_data_from_txt_abs(r"Outputs\Des\20260910\Nanodots_dilution\10x.csv")
data_100x = get_data_from_txt_abs(r"Outputs\Des\20260910\Nanodots_dilution\100x.csv")
# data_500x = get_data_from_txt_abs(r"Outputs\20260910\Nanodots_dilution\500x.csv")

data_1x_concentration = au0_concentration(data_1x["Wavelength"], data_1x["Absorbance"])
data_10x_concentration = au0_concentration(data_10x["Wavelength"], data_10x["Absorbance"])
data_100x_concentration = au0_concentration(data_100x["Wavelength"], data_100x["Absorbance"])
# data_500x_concentration = au0_concentration(data_500x["Wavelength"], data_500x["Absorbance"])

print(f"1x concentration:{data_1x_concentration:.4f} mM")
print(f"10x concentration:{data_10x_concentration:.4f} mM")
print(f"100x concentration:{data_100x_concentration:.4f} mM")
# print(f"500x concentration:{data_500x_concentration:.4f} mM")
