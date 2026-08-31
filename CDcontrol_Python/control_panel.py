"""
Class to draw tkinter gui to control SM440 handheld CCD and K10CR2 Thorlabs motorized mount
Author: Des De Borger
Last modified: 27/08/2026
"""

import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk

from motor_control import K10CR2
from spectrometer_control import Spectrometer

class ControlPanel(tk.Tk):
    def __init__(self):
        super().__init__()

        try:
            self.spec = Spectrometer()
        except Exception as e:
            print(f"Error connecting spectrometer: {e}")

        try:
            self.motor = K10CR2("55547014")
        except Exception as e:
            print(f"Error connecting motor: {e}") 

        self.title("CD Spectrometer Control Panel")
        self.geometry("620x650")

        # Connect devices
        self.connection_panel = tk.LabelFrame(self, text="Connect Devices")
        self.connection_panel.pack(padx=10, pady=10, fill="both")

        self.connect_motor_btn = tk.Button(self.connection_panel, text="Connect Motor", command=self.connect_motor)
        self.connect_motor_btn.grid(row=0, column=0, padx=10, pady=5)

        self.connect_spec_btn = tk.Button(self.connection_panel, text="Connect Spectrometer", command=self.connect_spectrometer)
        self.connect_spec_btn.grid(row=0, column=1, padx=10, pady=5)

        # Motor Control
        self.motor_control_panel = tk.LabelFrame(self, text="K10CR2 Motorized Mount Control")
        self.motor_control_panel.pack(padx=10, pady=10, fill="both")

        self.home_motor = tk.Button(self.motor_control_panel, text="Home Motor", command=self.motor.home)
        self.home_motor.grid(row=0, column=0, padx=10, pady=5)

        self.move_position_entry = tk.Entry(self.motor_control_panel)
        self.move_position_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.move_position_entry.insert(0, "0")

        self.move_motor_button = tk.Button(self.motor_control_panel, text="Move", command=self.move_motor_click)
        self.move_motor_button.grid(row=1, column=0, padx=10, pady=5)

        # Spectrometer Control
        self.spectrometer_panel = tk.LabelFrame(self, text="SM440 Handheld CCD Control")
        self.spectrometer_panel.pack(padx=10, pady=10, fill="both")

        self.int_time_label = tk.Label(self.spectrometer_panel, text="Set Integration Time:")
        self.int_time_label.grid(row=0, column=0, padx=10, pady=5)

        self.int_time_entry = tk.Entry(self.spectrometer_panel)
        self.int_time_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.int_time_entry.insert(0, "3000")
        self.int_time_entry.bind("<Return>", self.set_int_time_click)

        self.set_int_time_btn = tk.Button(self.spectrometer_panel, text="Set", command=self.set_int_time_click)
        self.set_int_time_btn.grid(row=0, column=2, padx=5, pady=5)

        self.time_avg_label = tk.Label(self.spectrometer_panel, text="Set Time Average:")
        self.time_avg_label.grid(row=1, column=0, padx=10, pady=5)

        self.time_avg_entry = tk.Entry(self.spectrometer_panel)
        self.time_avg_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.time_avg_entry.insert(0, "1")
        self.time_avg_entry.bind("<Return>", self.set_time_avg_click)

        self.set_time_avg_btn = tk.Button(self.spectrometer_panel, text="Set", command=self.set_time_avg_click)
        self.set_time_avg_btn.grid(row=1, column=2, padx=5, pady=5)

        self.measure_spectrum = tk.Button(self.spectrometer_panel, text="Measure Spectrum", command=self.measure_spectrum_click)
        self.measure_spectrum.grid(row=0, column=3, padx=10, pady=5)

        self.filename_label = tk.Label(self.spectrometer_panel, text="Filename:")
        self.filename_label.grid(row=2, column=0, padx=10, pady=5)

        self.filename_entry = tk.Entry(self.spectrometer_panel)
        self.filename_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.filename_entry.insert(0, "spectrum")

        self.save_spectrum_btn = tk.Button(self.spectrometer_panel, text="Save Spectrum Data", command=self.save_data_spectrum_click)
        self.save_spectrum_btn.grid(row=3, column=0, padx=5, pady=5)

        self.plot_spectrum_btn = tk.Button(self.spectrometer_panel, text="Save Spectrum Plot", command=self.save_plot_spectrum_click)
        self.plot_spectrum_btn.grid(row=3, column=1, padx=5, pady=5)

        self.show_max_btn = tk.Button(self.spectrometer_panel, text="Show maximum value pixel", command=self.show_max_val_pixel)
<<<<<<< Updated upstream
        self.show_max_btn.grid(row=3, column=2, padx=5, pady=5)

    def connect_motor(self):
         self.motor = K10CR2("55547014")

    def connect_spectrometer(self):
        self.spec = Spectrometer()
=======
        self.show_max_btn.grid(row=3, column=1, padx=5, pady=5)
>>>>>>> Stashed changes

    def move_motor_click(self):
        try:
            position = float(self.move_position_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid number for position.")
            return
        self.motor.move(position, 60000)

    def set_int_time_click(self, event=None):
        try:
            value = int(self.int_time_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid integer for integration time.")
            return
        self.spec.set_int_time(value)

    def set_time_avg_click(self, event=None):
        try:
            value = int(self.time_avg_entry.get())
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid integer for time average.")
            return
        self.spec.set_time_avg(value)

    def measure_spectrum_click(self):
        self.spec.measure()
        self.spec.plot_spectrum_pixels()

    def save_data_spectrum_click(self):
        if not self.filename_entry.get().strip():
                    tk.messagebox.showerror("Error", "Please enter a filename.")
                    return
        filename = "Outputs/" + self.filename_entry.get().strip()
        self.spec.save_spectrum(filename)

    def save_plot_spectrum_click(self):
        if not self.filename_entry.get().strip():
                    tk.messagebox.showerror("Error", "Please enter a filename.")
                    return
        filename = "Outputs/" + self.filename_entry.get().strip()
        self.spec.plot_spectrum(filename, show=False)

    def show_max_val_pixel(self):
<<<<<<< Updated upstream
            max_pixel = np.argmax(self.spec.spectrum)
            tk.messagebox.showinfo("Max Pixel", f"Maximum intensity at pixel {max_pixel}")
=======
        max_intensity = np.max(self.spec.spectrum)
        max_pixel = np.argmax(self.spec.spectrum)
        tk.messagebox.showinfo("Max Pixel", f"Maximum intensity at pixel {max_pixel}")
>>>>>>> Stashed changes

if __name__ == "__main__":
    app = ControlPanel()
    app.mainloop()