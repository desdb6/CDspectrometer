"""
Class to control Spectral Products SM440 handheld CCD
Author: Des De Borger
Last modified: 27/08/2026
"""

import os
from SP_SDK.SPdbUSBm import SPdbUSBm
import ctypes
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

# Define the DeviceInfo structure
class DeviceInfo(ctypes.Structure):
    _fields_ = [
        ("Model", ctypes.c_wchar * 256),        # Adjust string length
        ("Serial", ctypes.c_wchar * 256),       # Adjust string length
        ("nTOTPixelNo", ctypes.c_int),
        ("nRealPixelNo", ctypes.c_int),
        ("EffectivePixelIndex", ctypes.c_int),
        ("lIntTime", ctypes.c_long),
        ("lTimeAvg", ctypes.c_int),
        ("USBSpeed", ctypes.c_short),
        ("CCDType", ctypes.c_short)
    ]

class Spectrometer():
    def __init__(self):
        # Functions for using the DLL
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(self.current_dir, r'SP_SDK\SPdbUSBm.dll')
        self.spdb = SPdbUSBm(dll_path)

        # Make DeviceInfo struct
        self.DeviceInfo = DeviceInfo()

        # Connect and setup device
        self.check_connections()
        self.setup_device()

        # Set trigger mode to free run
        self.spdb.spSetIntMode(1, self.DeviceInfo.lIntTime, 0)

        # Calibrate wavelengths
        self.wavelength_calibration()

    def check_connections(self):
            sRtn = self.spdb.spTestAllChannels(0)
            if sRtn <= 0:
                raise Exception("Error, no devices detected!")
            elif sRtn != 1:
                raise Exception("Error, more than 1 device detected!")
            else:
                
                sRtn = self.spdb.spSetupAllChannels() # Set up all devices
                model_buffer = ctypes.create_string_buffer(256)
                serial_buffer = ctypes.create_string_buffer(256)
                sRtn = self.spdb.spDevInfo(model_buffer, serial_buffer, ctypes.c_short(0)) # Load model and serial numbers into variables
                self.DeviceInfo.Model = model_buffer.value.decode('utf-8') # Load variables into information structs
                self.DeviceInfo.Serial = serial_buffer.value.decode('utf-8')
                print("Device connected succesfully:")
                print(self.DeviceInfo.Model)

    def setup_device(self):
            # SM440-specific variables
            self.DeviceInfo.nTOTPixelNo = 3680
            self.DeviceInfo.nRealPixelNo = 3648
            self.DeviceInfo.EffectivePixelIndex = 32
            self.DeviceInfo.CCDType = ctypes.c_short(1)
            self.DeviceInfo.USBSpeed = ctypes.c_short(2)
            self.DeviceInfo.lIntTime = ctypes.c_long(30)
            self.DeviceInfo.lTimeAvg = ctypes.c_int(1)
    
            sRtn = self.spdb.spInitGivenChannel(self.DeviceInfo.CCDType, ctypes.c_short(0))
            if sRtn < 0:
                raise Exception("spInitGivenChannel Error")

    def set_int_time(self, t: int, verbatim: bool = False):
        self.DeviceInfo.lIntTime = (int)(t)
        sRtn = self.spdb.spSetIntEx(self.DeviceInfo.lIntTime, 0)
        if verbatim:
            print(f"Integration time set at {t}")

    def set_time_avg(self, k: int, verbatim: bool = False):
        self.DeviceInfo.lTimeAvg = (int)(k)
        if verbatim:
            print(f"Time averages set at {k}")

    def measure(self, verbatim: bool = True):
        # Allocate arrays
        DataArray = (ctypes.c_long * self.DeviceInfo.nTOTPixelNo)()
        tempArray = (ctypes.c_long * self.DeviceInfo.nTOTPixelNo)()

        # Data acquisition based on trigger mode
        loop_range = tqdm(range(self.DeviceInfo.lTimeAvg), desc="Scanning spectrum...") if verbatim else range(self.DeviceInfo.lTimeAvg)
        for _ in loop_range:
            sRtn = self.spdb.spReadDataEx(DataArray, 0) # CRUCIAL, this is the part that tells the spectrometer to expose and write to DataArray
            for j in range(self.DeviceInfo.nRealPixelNo): # Time averaging
                tempArray[j + self.DeviceInfo.EffectivePixelIndex] += DataArray[j + self.DeviceInfo.EffectivePixelIndex]

        if self.DeviceInfo.lTimeAvg == 1:
            pass
        else:
            for j in range(self.DeviceInfo.nRealPixelNo):
                DataArray[j + self.DeviceInfo.EffectivePixelIndex] = int(tempArray[j + self.DeviceInfo.EffectivePixelIndex] / self.DeviceInfo.lTimeAvg + 0.5) # 0.5 rounds correctly
                
        # Remove dark/reference pixels
        start = self.DeviceInfo.EffectivePixelIndex
        end = start + self.DeviceInfo.nRealPixelNo
        self.spectrum = np.array(DataArray[start:end])

    def wavelength_calibration(self):
        wavelength_values = [253.7, 313.2, 365.0, 404.7, 435.8, 546.1, 577.0, 579.1, 696.5, 763.5, 811.5, 912.3] # STILL NEEDS TO BE CALIBRATED
        pixel_values = [348, 465, 567, 643, 703, 910, 967, 971, 1186, 1306, 1392, 1570]

        # Fit a cubic polynomial: wavelength as a function of pixel number
        coefficients = np.polyfit(pixel_values, wavelength_values, deg=3)

        # Build a full pixel -> wavelength lookup table
        pixel_indices = np.arange(1, self.DeviceInfo.nRealPixelNo + 1)
        self.wavelengths = np.polyval(coefficients, pixel_indices)

    def save_spectrum(self, filename: str):
        filepath = os.path.join(self.current_dir, filename + ".txt")
        with open(filepath, "w") as file:
            file.write("Index\tIntensity\tIntensity\n")
            for j in range(self.DeviceInfo.nRealPixelNo):
                file.write(f"{j + 1}\t{self.wavelengths[j]}\t{self.spectrum[j]}\n")

        print(f"Saved spectrum to {filepath}")

    def plot_spectrum(self, filename: str = False, show: bool = True):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.wavelengths, self.spectrum, color="#2563eb", linewidth=1.2)

        ax.set_title(f"Measured spectrum", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel("Intensity (counts)", fontsize=11)

        ax.set_ybound(lower=0)

        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.margins(x=0.01)
        fig.tight_layout()

        if filename:
            fig.savefig(os.path.join(self.current_dir, filename + ".png"), dpi=200)

        if show:
            plt.show()
        else:
            plt.close()

if __name__ == "__main__":
    spec = Spectrometer()
    spec.set_int_time(3000)
    spec.set_time_avg(5)
    spec.measure()
    spec.save_spectrum("test")
    spec.plot_spectrum()