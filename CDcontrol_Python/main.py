"""
Class to draw tkinter gui to control SM440 handheld CCD and K10CR2 Thorlabs motorized mount
Author: Des De Borger
Last modified: 27/08/2026
"""

import threading
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox

from motor_control import K10CR2
from spectrometer_control import Spectrometer

# Offset angle where the linear polariser and fresnel rhomb axes are aligned to each other. This is calibrated using alignment.py
OFFSET_FRESNEL_ANGLE = np.mod(-8.6, 360)

# Dict for polarisation angles
POL_DICT = {"Horizontal": 0, "Vertical": 90, "LHC": 45, "RHC": 315}

# Weak signal cutoff, shades absorption spectra
WEAK_SIGNAL_CUTOFF = 500

class ControlPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CD Spectrometer Control Panel")
        self.geometry("1400x750")

        # Flags for clickable buttons
        self.motor_buttons_active = True
        self.spectrometer_buttons_active = True

        # Flag for moving motor
        self.motor_moving = False

        # Left column: control panels
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

        # ------------------------------------------------------------------
        # Connect Devices
        # ------------------------------------------------------------------
        self.connection_panel = tk.LabelFrame(self.controls_frame, text="Connect Devices")
        self.connection_panel.pack(padx=10, pady=10, fill="both")

        self.connect_motor_btn = tk.Button(self.connection_panel, text="Connect Motor", command=self.connect_motor)
        self.connect_motor_btn.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.connect_spec_btn = tk.Button(self.connection_panel, text="Connect Spectrometer", command=self.connect_spectrometer)
        self.connect_spec_btn.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # ------------------------------------------------------------------
        # Motor Control
        # ------------------------------------------------------------------
        self.motor_control_panel = tk.LabelFrame(self.controls_frame, text="K10CR2 Motorized Mount Control")
        self.motor_control_panel.pack(padx=10, pady=10, fill="both")

        # -- Manual Control sub-panel --
        self.motor_manual_control_panel = tk.LabelFrame(self.motor_control_panel, text="Manual Control Actions")
        self.motor_manual_control_panel.grid(row=0, column=0, padx=8, pady=4, sticky="ew")

        self.move_position_label = tk.Label(self.motor_manual_control_panel, text="Position (deg):")
        self.move_position_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.move_position_entry = tk.Entry(self.motor_manual_control_panel)
        self.move_position_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.move_position_entry.insert(0, "0")

        self.home_motor_button = tk.Button(self.motor_manual_control_panel, text="Home Motor", command=self.home_motor_click)
        self.home_motor_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.move_motor_button = tk.Button(self.motor_manual_control_panel, text="Move", command=self.move_motor_click)
        self.move_motor_button.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # -- Polarisation sub-panel --
        self.motor_polarisation_panel = tk.LabelFrame(self.motor_control_panel, text="Polarisation Actions")
        self.motor_polarisation_panel.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        self.alignment_angle_label = tk.Label(self.motor_polarisation_panel, text="Offset angle (deg):")
        self.alignment_angle_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        self.alignment_angle_show_box = tk.Entry(self.motor_polarisation_panel, width=8)
        self.alignment_angle_show_box.grid(row=1, column=2, padx=10, pady=5, sticky="ew")
        self.alignment_angle_show_box.insert(0, OFFSET_FRESNEL_ANGLE)
        self.alignment_angle_show_box.config(state="readonly")

        self.hor_pol_button = tk.Button(self.motor_polarisation_panel, text="Horizontal", command=lambda: self.move_motor_polarisation(pol="Horizontal"))
        self.hor_pol_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.vert_pol_button = tk.Button(self.motor_polarisation_panel, text="Vertical", command=lambda: self.move_motor_polarisation(pol="Vertical"))
        self.vert_pol_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.lhc_pol_button = tk.Button(self.motor_polarisation_panel, text="LHC", command=lambda: self.move_motor_polarisation(pol="LHC"))
        self.lhc_pol_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.rhc_pol_button = tk.Button(self.motor_polarisation_panel, text="RHC", command=lambda: self.move_motor_polarisation(pol="RHC"))
        self.rhc_pol_button.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # ------------------------------------------------------------------
        # Spectrometer Control
        # ------------------------------------------------------------------
        self.spectrometer_panel = tk.LabelFrame(self.controls_frame, text="SM440 Handheld CCD Control")
        self.spectrometer_panel.pack(padx=10, pady=10, fill="both")

        # -- Settings sub-panel --
        self.settings_panel = tk.LabelFrame(self.spectrometer_panel, text="Settings")
        self.settings_panel.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")

        self.int_time_label = tk.Label(self.settings_panel, text="Integration Time (ms):")
        self.int_time_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.int_time_entry = tk.Entry(self.settings_panel)
        self.int_time_entry.grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        self.int_time_entry.insert(0, "30")
        self.int_time_entry.bind("<Return>", self.set_spectrometer_settings_click)

        self.int_time_show_box = tk.Entry(self.settings_panel, state="readonly", width=8)
        self.int_time_show_box.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        self.time_avg_label = tk.Label(self.settings_panel, text="Time Average:")
        self.time_avg_label.grid(row=1, column=0, padx=8, pady=5, sticky="w")

        self.time_avg_entry = tk.Entry(self.settings_panel)
        self.time_avg_entry.grid(row=1, column=1, padx=8, pady=5, sticky="ew")
        self.time_avg_entry.insert(0, "1")
        self.time_avg_entry.bind("<Return>", self.set_spectrometer_settings_click)

        self.time_avg_show_box = tk.Entry(self.settings_panel, state="readonly", width=8)
        self.time_avg_show_box.grid(row=1, column=2, padx=8, pady=5, sticky="ew")

        self.set_settings_btn = tk.Button(self.settings_panel, text="Set", command=self.set_spectrometer_settings_click)
        self.set_settings_btn.grid(row=0, column=3, rowspan=2, padx=8, pady=5, sticky="ns")

        # -- Actions sub-panel --
        self.actions_panel = tk.LabelFrame(self.spectrometer_panel, text="Actions")
        self.actions_panel.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        self.measure_spectrum = tk.Button(self.actions_panel, text="Measure Spectrum", command=self.measure_spectrum_click)
        self.measure_spectrum.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.baseline_btn = tk.Button(self.actions_panel, text="Subtract Baseline", command=self.spec.measure_baseline)
        self.baseline_btn.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        self.live_view_btn = tk.Button(self.actions_panel, text="Start Live View", command=self.toggle_live_view)
        self.live_view_btn.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        # self.show_max_btn = tk.Button(self.actions_panel, text="Display Maximum Value Pixel", command=self.show_max_val_pixel)
        # self.show_max_btn.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        # -- Absorbance sub-panel --
        self.absorbance_panel = tk.LabelFrame(self.spectrometer_panel, text="Absorbance")
        self.absorbance_panel.grid(row=2, column=0, padx=8, pady=4, sticky="ew")

        self.measure_reference_spectrum = tk.Button(self.absorbance_panel, text="Measure Reference Spectrum", command=self.measure_reference_spectrum_click)
        self.measure_reference_spectrum.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.measure_absorbance_spectrum = tk.Button(self.absorbance_panel, text="Measure Absorbance Spectrum", command=self.measure_absorbance_spectrum_click)
        self.measure_absorbance_spectrum.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        # -- CD sub-panel --
        self.cd_panel = tk.LabelFrame(self.spectrometer_panel, text="Circular Dichroism")
        self.cd_panel.grid(row=3, column=0, padx=8, pady=4, sticky="ew")

        self.cd_cycles_label = tk.Label(self.cd_panel, text="# Cycles:")
        self.cd_cycles_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.cd_cycles_entry = tk.Entry(self.cd_panel)
        self.cd_cycles_entry.grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        self.cd_cycles_entry.insert(0, "3")
        self.cd_cycles_entry.bind("<Return>", self.set_cd_settings_click)

        self.cd_cycles_show_box = tk.Entry(self.cd_panel, state="readonly", width=8)
        self.cd_cycles_show_box.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        self.cd_cycles_btn = tk.Button(self.cd_panel, text="Set", command=self.set_cd_settings_click)
        self.cd_cycles_btn.grid(row=0, column=3, padx=8, pady=5, sticky="ns")

        self.measure_cd_spectrum = tk.Button(self.cd_panel, text="Measure CD Spectrum", command=self.measure_cd_spectrum_click)
        self.measure_cd_spectrum.grid(row=1, column=0, padx=8, pady=5, sticky="ew")

        # -- Save sub-panel --
        self.save_panel = tk.LabelFrame(self.spectrometer_panel, text="Save")
        self.save_panel.grid(row=4, column=0, padx=8, pady=(4, 8), sticky="ew")

        self.filename_label = tk.Label(self.save_panel, text="Filename:")
        self.filename_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.filename_entry = tk.Entry(self.save_panel)
        self.filename_entry.grid(row=0, column=1, columnspan=2, padx=8, pady=5, sticky="ew")
        self.filename_entry.insert(0, "spectrum")

        self.save_spectrum_btn = tk.Button(self.save_panel, text="Save Spectrum Data", command=self.save_data_spectrum_click)
        self.save_spectrum_btn.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        self.plot_spectrum_btn = tk.Button(self.save_panel, text="Save Spectrum Plot", command=self.save_plot_spectrum_click)
        self.plot_spectrum_btn.grid(row=1, column=2, padx=8, pady=5, sticky="ew")

        # ------------------------------------------------------------------
        # Live Spectrometer View
        # ------------------------------------------------------------------
        self.live_view_active = False

        self.fig = Figure(figsize=(5.5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot([], [], color="#2563eb", linewidth=1.2)
        self.ax.set_title("Live Spectrophotometer View", fontsize=14)
        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity (counts)")
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.set_xlim(np.min(self.spec.wavelengths), np.max(self.spec.wavelengths))
        self.ax.set_ylim(0, 2 ** 16)

        if self.spec.broken_wavelength_range is not None:
            self.ax.fill_between(
                self.spec.wavelengths, 0, 2 ** 16,
                where=self.spec.broken_wavelength_mask,
                color="#ff3838", alpha=0.5,
                label='Malfunctioning pixel range'
                )
            self.ax.legend(fontsize=6)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(padx=10, pady=10, fill="both", expand=True)

        # Home motor
        self.home_motor_click()

        # Set initial settings
        self.set_spectrometer_settings_click()
        self.set_cd_settings_click()

    def toggle_motor_buttons(self):
        if self.motor_buttons_active:
            self.move_motor_button.config(state="disabled")
            self.home_motor_button.config(state="disabled")
            self.hor_pol_button.config(state="disabled")
            self.vert_pol_button.config(state="disabled")
            self.lhc_pol_button.config(state="disabled")
            self.rhc_pol_button.config(state="disabled")
            self.motor_buttons_active = False
        elif not self.motor_buttons_active:
            self.move_motor_button.config(state="normal")
            self.home_motor_button.config(state="normal")
            self.hor_pol_button.config(state="normal")
            self.vert_pol_button.config(state="normal")
            self.lhc_pol_button.config(state="normal")
            self.rhc_pol_button.config(state="normal")
            self.motor_buttons_active = True

    def toggle_spectrometer_buttons(self):
        if self.spectrometer_buttons_active:
            self.measure_spectrum.config(state="disabled")
            self.baseline_btn.config(state="disabled")
            self.live_view_btn.config(state="disabled")
            self.measure_reference_spectrum.config(state="disabled")
            self.measure_absorbance_spectrum.config(state="disabled")
            self.measure_cd_spectrum.config(state="disabled")
            self.motor_buttons_active = False
        elif not self.spectrometer_buttons_active:
            self.measure_spectrum.config(state="normal")
            self.baseline_btn.config(state="normal")
            self.live_view_btn.config(state="normal")
            self.measure_reference_spectrum.config(state="normal")
            self.measure_absorbance_spectrum.config(state="normal")
            self.measure_cd_spectrum.config(state="normal")
            self.motor_buttons_active = True

    def connect_motor(self):
         self.motor = K10CR2("55547014")

    def connect_spectrometer(self):
        self.spec = Spectrometer()

    def home_motor_click(self):
        if self.motor_moving:
            return  # ignore clicks while a move is already in progress

        self.motor_moving = True
        self.toggle_motor_buttons()

        def worker():
            try:
                self.motor.home()
            finally:
                self.motor_moving = False
                self.toggle_motor_buttons()

        threading.Thread(target=worker, daemon=True).start()

    def move_motor_click(self):
            try:
                position = float(self.move_position_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for position.")
                return
    
            if self.motor_moving:
                return  # ignore clicks while a move is already in progress
    
            self.motor_moving = True
            self.toggle_motor_buttons()
    
            def worker():
                try:
                    self.motor.move(position, 60000)
                finally:
                    self.motor_moving = False
                    self.toggle_motor_buttons()
    
            threading.Thread(target=worker, daemon=True).start()

    def move_motor_polarisation(self, pol: str):
        position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT[pol], 360)

        if self.motor_moving:
            return  # ignore clicks while a move is already in progress

        self.motor_moving = True
        self.toggle_motor_buttons()

        def worker():
            try:
                self.motor.move(position, 60000)
            finally:
                self.motor_moving = False
                self.toggle_motor_buttons()

        threading.Thread(target=worker, daemon=True).start()

    def set_spectrometer_settings_click(self, event=None):
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

        self.update_motor_displays(true_t_int_val, t_avg_val) # Show settings in display boxes

    def update_motor_displays(self, t_int: float, t_avg: int):
        self.int_time_show_box.config(state="normal")
        self.int_time_show_box.delete(0, tk.END)
        self.int_time_show_box.insert(0, str(t_int))
        self.int_time_show_box.config(state="readonly")

        self.time_avg_show_box.config(state="normal")
        self.time_avg_show_box.delete(0, tk.END)
        self.time_avg_show_box.insert(0, str(t_avg))
        self.time_avg_show_box.config(state="readonly")

    def measure_spectrum_click(self):
        if not self.live_view_active:
            self.spec.measure()
        else:
            self.toggle_live_view()

        self.spec.plot_spectrum()
        self.cur_spectrum = self.spec.spectrum

    def measure_reference_spectrum_click(self):
        if not self.live_view_active:
            self.spec.measure()
        else:
            self.toggle_live_view()

        self.ref_spectrum = self.spec.spectrum
        self.weak_signal_mask = (self.ref_spectrum < WEAK_SIGNAL_CUTOFF)

    def measure_absorbance_spectrum_click(self):
        if not self.live_view_active:
            self.spec.measure()
        else:
            self.toggle_live_view()

        self.absor_spectrum = absorbance(self.ref_spectrum, self.spec.spectrum)
        self.cur_spectrum = self.absor_spectrum
        self.plot_absorbance_spectrum()

    def set_cd_settings_click(self, event=None):
        try:
            self.cd_cycles = int(self.cd_cycles_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for amount of cycles.")
            return

        self.cd_cycles_show_box.config(state="normal")
        self.cd_cycles_show_box.delete(0, tk.END)
        self.cd_cycles_show_box.insert(0, str(self.cd_cycles))
        self.cd_cycles_show_box.config(state="readonly")
        
    def measure_cd_spectrum_click(self):
        if self.motor_moving:
            return

        self.motor_moving = True
        self.toggle_motor_buttons()

        def worker():
            try:
                self.motor.home()
                
                temp_lhc_intensities = np.zeros_like(self.spec.spectrum)
                temp_rhc_intensities = np.zeros_like(self.spec.spectrum)
                
                for _ in range(self.cd_cycles):
                    # Left handed spectrum
                    position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["LHC"], 360)
                    self.motor.move(position, 60000)
                    self.spec.measure()
                    temp_lhc_intensities = temp_lhc_intensities + self.spec.spectrum

                    # Right handed spectrum
                    position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["RHC"], 360)
                    self.motor.move(position, 60000)
                    self.spec.measure()
                    self.rhc_intensities = self.spec.spectrum
                    temp_rhc_intensities = temp_rhc_intensities + self.spec.spectrum

                self.lhc_intensities = temp_lhc_intensities / self.cd_cycles
                self.rhc_intensities = temp_rhc_intensities / self.cd_cycles

                # CD signal
                self.cd_spectrum = ellipticity_millideg(self.lhc_intensities, self.rhc_intensities)

                self.after(0, self.plot_cd_spectrum)
            finally:
                self.motor_moving = False
                self.after(0, self.toggle_motor_buttons)
                self.cur_spectrum = self.cd_spectrum

        threading.Thread(target=worker, daemon=True).start()

    def save_data_spectrum_click(self):
        if not self.filename_entry.get().strip():
                    messagebox.showerror("Error", "Please enter a filename.")
                    return
        filename = "Outputs/" + self.filename_entry.get().strip()
        with open(filename, "w") as file:
            file.write("Index\tWavelength\tIntensity\n")
            for j in range(self.spec.DeviceInfo.nRealPixelNo):
                file.write(f"{j + 1}\t{self.spec.wavelengths[j]}\t{self.cur_spectrum[j]}\n")

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

    def update_live_view(self):
        if not self.live_view_active:
            return
        self.spec.measure(verbatim=False)
        self.line.set_data(self.spec.wavelengths, self.spec.spectrum)
        self.canvas.draw_idle()
        self.after(1, self.update_live_view)  # measure() itself paces this via lIntTime

    def plot_absorbance_spectrum(self, filename: str = False, show: bool = True):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.spec.wavelengths, self.absor_spectrum, color="#2563eb", linewidth=1.2)
        ax.fill_between(
            self.spec.wavelengths, 0, 1,
            where=self.weak_signal_mask,
            color="#848282ff", alpha=0.5,
            label=f'Weak signal range (Counts < {WEAK_SIGNAL_CUTOFF})',
            transform=ax.get_xaxis_transform()  # y in axes-fraction coords, not data coords
            )

        if self.spec.broken_wavelength_range is not None:
            ax.fill_between(
                self.spec.wavelengths, 0, 1,
                where=self.spec.broken_wavelength_mask,
                color="#ff3838", alpha=0.5,
                label='Malfunctioning pixel range',
                transform=ax.get_xaxis_transform()  # y in axes-fraction coords, not data coords
                )
            ax.legend()

        ax.set_title(f"Measured absorbance spectrum", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel("Absorbance", fontsize=11)

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

    def plot_cd_spectrum(self, filename: str = False, show: bool = True):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.spec.wavelengths, self.cd_spectrum, color="#2563eb", linewidth=1.2)
        ax.fill_between(
            self.spec.wavelengths, 0, 1,
            where=self.weak_signal_mask,
            color="#848282ff", alpha=0.5,
            label=f'Weak signal range (Counts < {WEAK_SIGNAL_CUTOFF})',
            transform=ax.get_xaxis_transform()  # y in axes-fraction coords, not data coords
            )

        if self.spec.broken_wavelength_range is not None:
            ax.fill_between(
                self.spec.wavelengths, 0, 1,
                where=self.spec.broken_wavelength_mask,
                color="#ff3838", alpha=0.5,
                label='Malfunctioning pixel range',
                transform=ax.get_xaxis_transform()  # y in axes-fraction coords, not data coords
                )
            ax.legend()

        ax.set_title(f"Measured Circular Dichroism spectrum", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel("CD (mdeg)", fontsize=11)

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

    def plot_ellipticity_spectrum(self, filename: str = False, show: bool = True):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.spec.wavelengths, self.ellipticity_spectrum, color="#2563eb", linewidth=1.2)

        if self.spec.broken_wavelength_range is not None:
            ax.fill_between(
                self.spec.wavelengths, 0, 1,
                where=self.spec.broken_wavelength_mask,
                color="#ff3838", alpha=0.5,
                label='Malfunctioning pixel range',
                transform=ax.get_xaxis_transform()  # y in axes-fraction coords, not data coords
                )
            ax.legend()

        ax.set_title(f"Measured Ellipticity spectrum", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel("Ellipticity", fontsize=11)

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

def absorbance(intensity_0: float, intensity: float):
    """Calculate absorbance"""
    return np.log10(intensity_0 / intensity)

def molar_absorbance(intensity_0: float, intensity: float, c: float, l: float):
    """Calculate molar absorbance"""
    return absorbance(intensity_0, intensity) / (c * l)

def delta_absorbance(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as absorbance difference"""
    return np.log10(intensity_l / intensity_r)

def delta_molar_absorbance(intensity_l: float, intensity_r: float, c: float, l: float):
    """Calculate CD signal expressed as molar absorbance difference"""
    return delta_absorbance(intensity_l, intensity_r) / (c * l)

def ellipticity_deg(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as ellipticity"""
    return delta_absorbance(intensity_l, intensity_r) * np.log(10) * 45 / np.pi

def ellipticity_millideg(intensity_l: float, intensity_r: float):
    """Calculate CD signal expressed as ellipticity in millidegrees"""
    return 1000 * ellipticity_deg(intensity_l, intensity_r)

if __name__ == "__main__":
    app = ControlPanel()
    app.mainloop()