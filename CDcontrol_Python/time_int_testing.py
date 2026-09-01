"""
Script to figure out time unit conversion as it is wrong in the SDK documentation.
Author: Des De Borger
Last modified: 01/09/2026
"""

from time import time
import numpy as np

from tqdm import tqdm

from spectrometer_control import Spectrometer, ms_to_real_int_time

OUTPUT_FILE = r"Outputs\int_time_calibration.txt"

def get_real_time(t: float, spec: Spectrometer):
    spec.set_int_time(t, convert_units=False)
    tick = time()
    spec.measure(verbatim=False)
    tock = time()
    return tock - tick

def lin_reg(file):
    data = np.loadtxt(file, skiprows=1)
    x = data[:, 0]  # lIntTime
    y = data[:, 1]  # Real time

    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - (slope * x + intercept)
    sse = np.sum(resid ** 2)
    r_squared = 1 - sse / np.sum((y - y.mean()) ** 2)
    return slope, intercept, r_squared


if __name__ == "__main__":
    spec = Spectrometer()
    spec.set_time_avg(1)
    input_times = np.linspace(1000, 0, 50)
    real_times = np.zeros_like(input_times)
    for i, t in tqdm(enumerate(input_times)):
        real_times[i] = get_real_time(t, spec)

    data = np.column_stack((input_times, real_times))
    np.savetxt(
        OUTPUT_FILE,
        data,
        header="lIntTime\tReal_time_s",
        delimiter="\t",
        fmt="%.6f",
    )

    conversion_factor, intercept, r = lin_reg(OUTPUT_FILE)
    print("\nLinear Regression Results:")
    print(f"Conversion factor: {conversion_factor:.5e}")
    print(f"Offset: {intercept:.5e}")
    print(f"R**2: {r:.5e}")