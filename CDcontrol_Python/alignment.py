"""
Class to draw tkinter gui to control SM440 handheld CCD and K10CR2 Thorlabs motorized mount
Author: Des De Borger
Last modified: 27/08/2026
"""

import threading

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
import csv

from motor_control import K10CR2
from spectrometer_control import Spectrometer

class ControlPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CD Spectrometer Control Panel")
        self.geometry("1150x560")  # widen the window to fit both columns

        # Left column: holds all existing control panels
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side="left", fill="y", padx=5, pady=5)

        # Right column: live view plot
        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        try:
            self.spec = Spectrometer()
        except Exception as e:
            print(f"Error connecting spectrometer: {e}")

        try:
            self.motor = K10CR2("55547014")
        except Exception as e:
            print(f"Error connecting motor: {e}") 

        # Connect devices
        self.connection_panel = tk.LabelFrame(self.controls_frame, text="Connect Devices")
        self.connection_panel.pack(padx=10, pady=10, fill="both")

        self.connect_motor_btn = tk.Button(self.connection_panel, text="Connect Motor", command=self.connect_motor)
        self.connect_motor_btn.grid(row=0, column=0, padx=10, pady=5)

        self.connect_spec_btn = tk.Button(self.connection_panel, text="Connect Spectrometer", command=self.connect_spectrometer)
        self.connect_spec_btn.grid(row=0, column=1, padx=10, pady=5)

        # Motor Control
        self.motor_moving = False

        self.motor_control_panel = tk.LabelFrame(self.controls_frame, text="K10CR2 Motorized Mount Control")
        self.motor_control_panel.pack(padx=10, pady=10, fill="both")

        self.home_motor = tk.Button(self.motor_control_panel, text="Home Motor", command=self.motor.home)
        self.home_motor.grid(row=0, column=0, padx=10, pady=5)

        self.move_position_entry = tk.Entry(self.motor_control_panel)
        self.move_position_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.move_position_entry.insert(0, "0")

        self.move_motor_button = tk.Button(self.motor_control_panel, text="Move", command=self.move_motor_click)
        self.move_motor_button.grid(row=1, column=0, padx=10, pady=5)

        # Spectrometer Control
        self.spectrometer_panel = tk.LabelFrame(self.controls_frame, text="SM440 Handheld CCD Control")
        self.spectrometer_panel.pack(padx=10, pady=10, fill="both")

        self.int_time_label = tk.Label(self.spectrometer_panel, text="Set Integration Time (ms):")
        self.int_time_label.grid(row=0, column=0, padx=10, pady=5)

        self.int_time_entry = tk.Entry(self.spectrometer_panel)
        self.int_time_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.int_time_entry.insert(0, "30")
        self.int_time_entry.bind("<Return>", self.set_settings_click)

        self.int_time_show_box = tk.Entry(self.spectrometer_panel, state="readonly")
        self.int_time_show_box.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        self.set_int_time_btn = tk.Button(self.spectrometer_panel, text="Set", command=self.set_settings_click)
        self.set_int_time_btn.grid(row=0, column=3, padx=5, pady=5)

        self.time_avg_label = tk.Label(self.spectrometer_panel, text="Set Time Average:")
        self.time_avg_label.grid(row=1, column=0, padx=10, pady=5)

        self.time_avg_entry = tk.Entry(self.spectrometer_panel)
        self.time_avg_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.time_avg_entry.insert(0, "1")
        self.time_avg_entry.bind("<Return>", self.set_settings_click)

        self.time_avg_show_box = tk.Entry(self.spectrometer_panel, state="readonly")
        self.time_avg_show_box.grid(row=1, column=2, padx=10, pady=5, sticky="ew")

        self.set_settings_click() # Set initial settings

        self.measure_spectrum = tk.Button(self.spectrometer_panel, text="Measure Spectrum", command=self.measure_spectrum_click)
        self.measure_spectrum.grid(row=3, column=0, padx=10, pady=5)

        self.filename_label = tk.Label(self.spectrometer_panel, text="Filename:")
        self.filename_label.grid(row=2, column=0, padx=10, pady=5)

        self.filename_entry = tk.Entry(self.spectrometer_panel)
        self.filename_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.filename_entry.insert(0, "spectrum")

        self.save_spectrum_btn = tk.Button(self.spectrometer_panel, text="Save Spectrum Data", command=self.save_data_spectrum_click)
        self.save_spectrum_btn.grid(row=3, column=1, padx=5, pady=5)

        self.plot_spectrum_btn = tk.Button(self.spectrometer_panel, text="Save Spectrum Plot", command=self.save_plot_spectrum_click)
        self.plot_spectrum_btn.grid(row=3, column=2, padx=5, pady=5)

        self.show_max_btn = tk.Button(self.spectrometer_panel, text="Display Maximum Value Pixel", command=self.show_max_val_pixel)
        self.show_max_btn.grid(row=3, column=3, padx=5, pady=5)

        self.baseline_btn = tk.Button(self.spectrometer_panel, text="Measure Baseline", command=self.spec.measure_baseline)
        self.baseline_btn.grid(row=4, column=0, padx=10, pady=5)

        # Live Spectrometer View
        self.live_view_active = False
        self.fill = None

        self.fig = Figure(figsize=(5.5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], [], color="#2563eb", linewidth=1.2)
        self.ax.set_title("Live Spectrophotometer View", fontsize=14)
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity (counts)")
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.set_xlim(np.min(self.spec.wavelengths), np.max(self.spec.wavelengths))
        self.ax.set_ylim(0, 2 ** 16)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(padx=10, pady=10, fill="both", expand=True)

        self.live_view_btn = tk.Button(self.spectrometer_panel, text="Start Live View", command=self.toggle_live_view)
        self.live_view_btn.grid(row=5, column=0, padx=10, pady=5)

        self.area_label = tk.Label(self.spectrometer_panel, text="Area Under Curve (650-900nm):")
        self.area_label.grid(row=6, column=0, padx=10, pady=5)

        self.area_show_box = tk.Entry(self.spectrometer_panel, state="readonly")
        self.area_show_box.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

    def connect_motor(self):
         self.motor = K10CR2("55547014")

    def connect_spectrometer(self):
        self.spec = Spectrometer()

    def move_motor_click(self):
        try:
            position = float(self.move_position_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for position.")
            return

        if self.motor_moving:
            return  # ignore clicks while a move is already in progress

        self.motor_moving = True
        self.move_motor_button.config(state="disabled")

        def worker():
            try:
                self.motor.move(position, 60000)
            finally:
                self.motor_moving = False
                self.after(0, lambda: self.move_motor_button.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def set_settings_click(self, event=None):
        try:
            t_int_val = float(self.int_time_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for integration time.")
            return

        try:
            t_avg_val = int(self.time_avg_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for time average.")
            return
        
        self.spec.set_int_time(t_int_val) # Push int time to spectrometer
        true_t_int_val = int(t_int_val * 50) / 50 # Calculate actual integration time, stepped by 20 microseconds

        self.spec.set_time_avg(t_avg_val)

        self.update_displays(true_t_int_val, t_avg_val) # Show settings in display boxes

    def update_displays(self, t_int: float, t_avg: int):
        self.int_time_show_box.config(state="normal")
        self.int_time_show_box.delete(0, tk.END)
        self.int_time_show_box.insert(0, str(t_int))
        self.int_time_show_box.config(state="readonly")

        self.time_avg_show_box.config(state="normal")
        self.time_avg_show_box.delete(0, tk.END)
        self.time_avg_show_box.insert(0, str(t_avg))
        self.time_avg_show_box.config(state="readonly")

    def save_data_spectrum_click(self):
        if not self.filename_entry.get().strip():
                    messagebox.showerror("Error", "Please enter a filename.")
                    return
        filename = "Outputs/" + self.filename_entry.get().strip()
        self.spec.save_spectrum(filename)

    def save_plot_spectrum_click(self):
        if not self.filename_entry.get().strip():
                    messagebox.showerror("Error", "Please enter a filename.")
                    return
        filename = "Outputs/" + self.filename_entry.get().strip()
        self.spec.plot_spectrum(filename, show=False)

    def show_max_val_pixel(self):
            max_pixel = np.argmax(self.spec.spectrum)
            messagebox.showinfo("Max Pixel", f"Maximum intensity at pixel {max_pixel}")

    def toggle_live_view(self):
        self.live_view_active = not self.live_view_active
        self.live_view_btn.config(text="Stop Live View" if self.live_view_active else "Start Live View")
        if self.live_view_active:
            self.update_live_view()

    def compute_area(self, wavelengths: np.array, intensities: np.array, lo: float = 650, hi: float = 900) -> float:
        mask = (wavelengths >= lo) & (wavelengths <= hi)
        if not np.any(mask):
            return 0.0
        self.area = float(np.trapz(intensities[mask], wavelengths[mask]))
        return self.area

    def update_area_display(self, area: float):
        self.area_show_box.config(state="normal")
        self.area_show_box.delete(0, tk.END)
        self.area_show_box.insert(0, f"{area:.2f}")
        self.area_show_box.config(state="readonly")

    def update_fill(self, wavelengths: np.array, intensities: np.array, lo: float = 650, hi: float = 900):
        if self.fill is not None:
            self.fill.remove()
        mask = (wavelengths >= lo) & (wavelengths <= hi)
        self.fill = self.ax.fill_between(wavelengths, intensities, 0, where=mask,
                                        color="#2563eb", alpha=0.25, interpolate=True)

    def measure_spectrum_click(self):
        if not self.live_view_active:
            self.spec.measure()
        else:
            self.toggle_live_view()

        self.spec.plot_spectrum()

        self.area = self.compute_area(self.spec.wavelengths, self.spec.spectrum)
        self.update_area_display(self.area)

    def update_live_view(self):
        if not self.live_view_active:
            return
        self.spec.measure(verbatim=False)
        self.line.set_data(self.spec.wavelengths, self.spec.spectrum)
        self.update_fill(self.spec.wavelengths, self.spec.spectrum)

        area = self.compute_area(self.spec.wavelengths, self.spec.spectrum)
        self.update_area_display(area)

        self.canvas.draw_idle()
        self.after(1, self.update_live_view)  # measure() itself paces this via lIntTime

    def plot_spectrum(self, wavelengths: np.array, intensities: np.array):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(wavelengths, intensities, color="#2563eb", linewidth=1.2)

        mask = (wavelengths >= 650) & (wavelengths <= 900)
        ax.fill_between(wavelengths, intensities, 0, where=mask,
                        color="#2563eb", alpha=0.25, interpolate=True)

        ax.set_title(f"Measured spectrum", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel("Intensity (counts)", fontsize=11)

        ax.set_ybound(lower=0)

        ax.grid(True, linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        ax.margins(x=0.01)
        fig.tight_layout()

if __name__ == "__main__":
    app = ControlPanel()

    app.spec.set_int_time(80)
    app.spec.set_time_avg(20)

    app.motor.home()

    angles = np.linspace(81, 82, 101)

    with open('Outputs/fast_axis_calibration_very_fine.csv', 'w', newline='') as csvfile:
        fieldnames = ['Angle', 'Area under curve']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for angle in angles:
            app.motor.move(angle, 60000)
            app.spec.measure()
            app.compute_area(app.spec.wavelengths, app.spec.spectrum)
            writer.writerow({'Angle': float(angle), 'Area under curve': float(app.area)})
