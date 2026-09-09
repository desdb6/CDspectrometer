"""
Class to draw tkinter gui to control SM440 handheld CCD and K10CR2 Thorlabs motorized mount
Author: Des De Borger
Last modified: 27/08/2026
"""

import threading
import os
import csv

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox

from motor_control import K10CR2
from spectrometer_control import Spectrometer
from utils import *

# Offset angle where the linear polarizer and fresnel rhomb axes are aligned to each other. This is calibrated using alignment.py
OFFSET_FRESNEL_ANGLE = np.mod(107.41 - 90, 360)

# Dict for polarization angles
POL_DICT = {"Horizontal": 0, "Vertical": 90, "LHC": 45, "RHC": 315}

# Weak signal cutoff, shades absorption spectra
WEAK_SIGNAL_CUTOFF = 500

class ControlPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CD Spectrometer Control Panel")
        self.geometry("1400x850")
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Initialise spectra
        self.cur_spectrum = None

        self.ref_spectrum = None # Absorbance spectroscopy
        self.sample_spectrum = None
        self.abs_spectrum = None

        self.ref_lhc_intensities = None # CD spectroscopy
        self.ref_rhc_intensities = None
        self.lhc_intensities = None
        self.rhc_intensities = None
        self.cd_ref_spectrum = None
        self.cd_spectrum = None
        self.cd_spectrum_millideg = None
        self.avg_abs_spectrum = None
        self.g_factor = None

        # Flag for current spectrum kind
        self.cur_spectrum_kind = None

        # Flags for clickable buttons
        self.motor_buttons_active = True
        self.spectrometer_buttons_active = True

        # Flags for busy components
        self.motor_moving = False
        self.spectrometer_busy = False

        # Flag for dark count
        self.dark_count_subtracted = False

        # Left column: control panels
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side="left", fill="y", padx=5, pady=5)

        # Right column: live view plot
        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        try:
            self.spec = Spectrometer()
        except Exception as e:
            self.spec = None
            messagebox.showwarning("Spectrometer not connected", f"Could not connect to spectrometer:\n{e}")

        try:
            self.motor = K10CR2("55547014")
        except Exception as e:
            self.motor = None
            messagebox.showwarning("Motorized mount not connected", f"Could not connect to motor:\n{e}")

        # ------------------------------------------------------------------
        # Connect Devices
        # ------------------------------------------------------------------
        self.connection_panel = tk.LabelFrame(self.controls_frame, text="Connect Devices")
        self.connection_panel.pack(padx=10, pady=5, fill="both")

        self.connect_motor_btn = tk.Button(self.connection_panel, text="Connect Motor", command=self.connect_motor)
        self.connect_motor_btn.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.connect_spec_btn = tk.Button(self.connection_panel, text="Connect Spectrometer", command=self.connect_spectrometer)
        self.connect_spec_btn.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            self.connection_panel, textvariable=self.status_var,
            anchor="w", fg="#444444"
            )
        self.status_label.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        # Let the status column absorb extra horizontal space rather than the buttons stretching
        self.connection_panel.grid_columnconfigure(2, weight=1)

        # ------------------------------------------------------------------
        # Motor Control
        # ------------------------------------------------------------------
        self.motor_control_panel = tk.LabelFrame(self.controls_frame, text="K10CR2 Motorized Mount Control")
        self.motor_control_panel.pack(padx=10, pady=5, fill="both")

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

        # -- Polarization sub-panel --
        self.motor_polarization_panel = tk.LabelFrame(self.motor_control_panel, text="Polarization Actions")
        self.motor_polarization_panel.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        self.alignment_angle_label = tk.Label(self.motor_polarization_panel, text="Offset angle (deg):")
        self.alignment_angle_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        self.alignment_angle_show_box = tk.Entry(self.motor_polarization_panel, width=8)
        self.alignment_angle_show_box.grid(row=1, column=2, padx=10, pady=5, sticky="ew")
        self.alignment_angle_show_box.insert(0, OFFSET_FRESNEL_ANGLE)
        self.alignment_angle_show_box.config(state="readonly")

        self.hor_pol_button = tk.Button(self.motor_polarization_panel, text="Horizontal", command=lambda: self.move_motor_polarization(pol="Horizontal"))
        self.hor_pol_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.vert_pol_button = tk.Button(self.motor_polarization_panel, text="Vertical", command=lambda: self.move_motor_polarization(pol="Vertical"))
        self.vert_pol_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.lhc_pol_button = tk.Button(self.motor_polarization_panel, text="LHC", command=lambda: self.move_motor_polarization(pol="LHC"))
        self.lhc_pol_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.rhc_pol_button = tk.Button(self.motor_polarization_panel, text="RHC", command=lambda: self.move_motor_polarization(pol="RHC"))
        self.rhc_pol_button.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # ------------------------------------------------------------------
        # Spectrometer Control
        # ------------------------------------------------------------------
        self.t_int_val = 30
        self.t_avg_val = 1

        self.spectrometer_panel = tk.LabelFrame(self.controls_frame, text="SM440 Handheld CCD Control")
        self.spectrometer_panel.pack(padx=10, pady=5, fill="both")

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

        self.measure_spectrum = tk.Button(self.actions_panel, text="Measure Reference Spectrum", command=self.measure_spectrum_click)
        self.measure_spectrum.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.dark_count_btn = tk.Button(self.actions_panel, text="Subtract Dark Counts", command=self.measure_dark_count)
        self.dark_count_btn.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        self.live_view_btn = tk.Button(self.actions_panel, text="Start Live View", command=self.toggle_live_view)
        self.live_view_btn.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        # self.show_max_btn = tk.Button(self.actions_panel, text="Display Maximum Value Pixel", command=self.show_max_val_pixel)
        # self.show_max_btn.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        # -- Absorbance sub-panel --
        self.absorbance_panel = tk.LabelFrame(self.spectrometer_panel, text="Absorbance")
        self.absorbance_panel.grid(row=2, column=0, padx=8, pady=4, sticky="ew")

        self.measure_absorbance_spectrum = tk.Button(self.absorbance_panel, text="Measure Absorbance Spectrum", command=self.measure_absorbance_spectrum_click)
        self.measure_absorbance_spectrum.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        # -- CD sub-panel --
        self.cd_panel = tk.LabelFrame(self.spectrometer_panel, text="Circular Dichroism")
        self.cd_panel.grid(row=3, column=0, padx=8, pady=4, sticky="ew")

        self.cd_cycles_label = tk.Label(self.cd_panel, text="# Cycles:")
        self.cd_cycles_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.cd_cycles_entry = tk.Entry(self.cd_panel)
        self.cd_cycles_entry.grid(row=0, column=1, padx=8, pady=5, sticky="ew")
        self.cd_cycles_entry.insert(0, "1")
        self.cd_cycles_entry.bind("<Return>", self.set_cd_settings_click)

        self.cd_cycles_show_box = tk.Entry(self.cd_panel, state="readonly", width=8)
        self.cd_cycles_show_box.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        self.cd_cycles_btn = tk.Button(self.cd_panel, text="Set", command=self.set_cd_settings_click)
        self.cd_cycles_btn.grid(row=0, column=3, padx=8, pady=5, sticky="ns")

        self.measure_cd_reference_btn = tk.Button(self.cd_panel, text="Measure CD Reference", command=self.measure_cd_reference_click)
        self.measure_cd_reference_btn.grid(row=1, column=0, padx=8, pady=5, sticky="ew")

        self.measure_cd_spectrum_btn = tk.Button(self.cd_panel, text="Measure CD Spectrum", command=self.measure_cd_spectrum_click)
        self.measure_cd_spectrum_btn.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        # -- Save sub-panel --
        self.save_panel = tk.LabelFrame(self.spectrometer_panel, text="Save")
        self.save_panel.grid(row=4, column=0, padx=8, pady=(4, 8), sticky="ew")

        self.filename_label = tk.Label(self.save_panel, text="Filename:")
        self.filename_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.filename_entry = tk.Entry(self.save_panel)
        self.filename_entry.grid(row=0, column=1, columnspan=2, padx=8, pady=5, sticky="ew")
        self.filename_entry.insert(0, "spectrum")

        self.save_spectrum_btn = tk.Button(self.save_panel, text="Save Spectrum Data", command=self.save_data_spectrum_click)
        self.save_spectrum_btn.grid(row=0, column=3, padx=8, pady=5, sticky="ew")

        # -- Plot sub-panel --
        self.plot_panel = tk.LabelFrame(self.spectrometer_panel, text="Plot")
        self.plot_panel.grid(row=5, column=0, padx=8, pady=(4, 8), sticky="ew")

        self.plot_ref_btn = tk.Button(self.plot_panel, text="Ref", command=self.save_plot_ref_click)
        self.plot_ref_btn.grid(row=0, column=0, padx=8, pady=5, sticky="ew")

        self.plot_abs_btn = tk.Button(self.plot_panel, text="Abs", command=self.save_plot_abs_click)
        self.plot_abs_btn.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        self.plot_abs_btn = tk.Button(self.plot_panel, text="Avg abs", command=self.save_plot_avg_abs_click)
        self.plot_abs_btn.grid(row=0, column=2, padx=8, pady=5, sticky="ew")

        self.plot_cd_ref_btn = tk.Button(self.plot_panel, text="CD Ref", command=self.save_plot_cd_ref_click)
        self.plot_cd_ref_btn.grid(row=0, column=3, padx=8, pady=5, sticky="ew")

        self.plot_cd_btn = tk.Button(self.plot_panel, text="CD", command=self.save_plot_cd_click)
        self.plot_cd_btn.grid(row=0, column=4, padx=8, pady=5, sticky="ew")

        self.plot_ellipticity_btn = tk.Button(self.plot_panel, text="Ellipticity", command=self.save_plot_ellipticity_click)
        self.plot_ellipticity_btn.grid(row=0, column=5, padx=8, pady=5, sticky="ew")

        self.plot_g_factor_btn = tk.Button(self.plot_panel, text="g-factor", command=self.save_plot_g_factor_click)
        self.plot_g_factor_btn.grid(row=0, column=6, padx=8, pady=5, sticky="ew")

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

        try:
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
        except AttributeError:
            # self.spec is None or missing expected attributes (not connected)
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.ax.text(
                0.5, 0.5, "Spectrometer not connected",
                ha="center", va="center", transform=self.ax.transAxes,
                fontsize=11, color="#888888"
                )

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(padx=10, pady=10, fill="both", expand=True)

        # Home motor
        if self.motor is not None:
            self.home_motor_click()

        # Set initial settings
        if self.spec is not None:
            self.set_spectrometer_settings_click()
        self.set_cd_settings_click()

        # Turn off buttons if not connected
        if self.motor is None:
            self.motor_buttons_active = True   # set to true, toggle turns it to false
            self.toggle_motor_buttons()

        if self.spec is None:
            self.spectrometer_buttons_active = True
            self.toggle_spectrometer_buttons()

    # ------------------------------------------------------------------
    # Toggle methods
    # ------------------------------------------------------------------

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
            self.dark_count_btn.config(state="disabled")
            self.live_view_btn.config(state="disabled")
            self.measure_absorbance_spectrum.config(state="disabled")
            self.measure_cd_spectrum_btn.config(state="disabled")
            self.measure_cd_reference_btn.config(state="disabled")
            self.spectrometer_buttons_active = False
        elif not self.spectrometer_buttons_active:
            self.measure_spectrum.config(state="normal")
            self.dark_count_btn.config(state="normal")
            self.live_view_btn.config(state="normal")
            self.measure_absorbance_spectrum.config(state="normal")
            self.measure_cd_spectrum_btn.config(state="normal")
            self.measure_cd_reference_btn.config(state="normal")
            self.spectrometer_buttons_active = True

    # ------------------------------------------------------------------
    # Connect methods
    # ------------------------------------------------------------------

    def connect_motor(self):
        try:
            self.motor = K10CR2("55547014")
        except Exception as e:
            self.motor = None
            messagebox.showerror("Error", f"Could not connect to motor:\n{e}")
            return

        self.set_status("Succesfully connected motor.")

        if not self.motor_buttons_active:
            self.toggle_motor_buttons()

    def connect_spectrometer(self):
        try:
            self.spec = Spectrometer()
        except Exception as e:
            self.spec = None
            messagebox.showerror("Error", f"Could not connect to spectrometer:\n{e}")
            return

        if not self.spectrometer_buttons_active:
            self.toggle_spectrometer_buttons()

        self.set_status("Succesfully connected spectrometer.")

        # Refresh the live-view plot now that self.spec is populated
        self.ax.clear()
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

        self.canvas.draw_idle()

    def set_status(self, text: str):
        """Thread-safe status update — always routes through the Tk main loop."""
        self.after(0, lambda: self.status_var.set(text))

    # ------------------------------------------------------------------
    # Motor control methods
    # ------------------------------------------------------------------

    def home_motor_click(self):
        if self.motor_moving:
            return  # ignore clicks while a move is already in progress

        self.motor_moving = True
        self.toggle_motor_buttons()

        def worker():
            try:
                self.set_status("Homing motor....")
                self.motor.home()
            finally:
                self.motor_moving = False
                self.after(0, self.toggle_motor_buttons)
                self.set_status("Motor homed")

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
                    self.set_status(f"Moving motor to {position}...")
                    self.motor.move(position, 60000)
                finally:
                    self.motor_moving = False
                    self.after(0, self.toggle_motor_buttons)
                    self.set_status(f"Motor moved to {position}")
    
            threading.Thread(target=worker, daemon=True).start()

    def move_motor_polarization(self, pol: str):
        position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT[pol], 360)

        if self.motor_moving:
            return  # ignore clicks while a move is already in progress

        self.motor_moving = True
        self.toggle_motor_buttons()

        def worker():
            try:
                self.set_status(f"Moving motor to {pol}...")
                self.motor.move(position, 60000)
            finally:
                self.motor_moving = False
                self.after(0, self.toggle_motor_buttons)
                self.set_status(f"Motor moved to {pol}")

        threading.Thread(target=worker, daemon=True).start()

    def update_motor_displays(self, t_int: float, t_avg: int):
        self.int_time_show_box.config(state="normal")
        self.int_time_show_box.delete(0, tk.END)
        self.int_time_show_box.insert(0, str(t_int))
        self.int_time_show_box.config(state="readonly")

        self.time_avg_show_box.config(state="normal")
        self.time_avg_show_box.delete(0, tk.END)
        self.time_avg_show_box.insert(0, str(t_avg))
        self.time_avg_show_box.config(state="readonly")

    # ------------------------------------------------------------------
    # Live view methods
    # ------------------------------------------------------------------

    def toggle_live_view(self):
        if self.new_t_int_val * self.new_t_avg_val > 1000 and not self.live_view_active:
            proceed = messagebox.askokcancel(
                "Long integration time",
                f"The expected time per spectrum is large ({self.new_t_int_val*self.new_t_avg_val:.1f}ms). "
                f"This can cause the program to lag when activating live view. Do you wish to proceed?."
            )
            if not proceed:
                return
            
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

    # ------------------------------------------------------------------
    # Spectrometer action panel methods
    # ------------------------------------------------------------------

    def set_spectrometer_settings_click(self, event=None):
        try:
            self.new_t_int_val = float(self.int_time_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for integration time.")
            return

        try:
            self.new_t_avg_val = int(self.time_avg_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for time average.")
            return

        if self.new_t_int_val * self.new_t_avg_val > 1000 and self.live_view_active:
            proceed = messagebox.askokcancel("Long integration time", f"The expected time per spectrum is large ({self.new_t_int_val*self.new_t_avg_val:.1f}ms) and live view is active. This can cause the program to lag. Do you wish to proceed?.")
            if not proceed:
                return

        if self.new_t_int_val != self.t_int_val: # Safeguard that the same settings are used for reference and absorbance spectra
            self.ref_spectrum = None
        
        self.spec.set_int_time(self.new_t_int_val) # Push int time to spectrometer
        true_t_int_val = int(self.new_t_int_val * 50) / 50 # Calculate actual integration time, stepped by 20 microseconds
        self.spec.set_time_avg(self.new_t_avg_val)

        self.update_motor_displays(true_t_int_val, self.new_t_avg_val) # Show settings in display boxes

        self.t_int_val = self.new_t_int_val
        self.t_avg_val = self.new_t_avg_val

        self.set_status(f"Pushed settings to spectrometer.")

    def measure_dark_count(self):
        self.spec.measure_dark_count()
        self.dark_count_subtracted = True
        self.set_status(f"Dark counts subtracted.")

    def measure_spectrum_click(self):

        if self.dark_count_subtracted == False:
            proceed = messagebox.askokcancel("Dark count not subtracted", "Dark counts have not been subtracted. Do you want to continue?") 
            if not proceed:
                return

        if self.live_view_active:
            self.toggle_live_view()

        if self.spectrometer_busy:
            return  # ignore clicks while a measurement is already in progress

        self.spectrometer_busy = True
        self.toggle_spectrometer_buttons()

        def worker():
            try:
                self.set_status(f"Measuring reference spectrum...")
                self.spec.measure()
                self.cur_spectrum = self.spec.spectrum.copy()
                self.ref_spectrum = self.spec.spectrum.copy()
                self.cur_spectrum_kind = "Reference"
                self.weak_signal_mask = (self.ref_spectrum < WEAK_SIGNAL_CUTOFF)
                self.after(0, self.spec.plot_spectrum)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Measurement failed:\n{e}"))
            finally:
                self.spectrometer_busy = False
                self.after(0, self.toggle_spectrometer_buttons)
                self.set_status(f"Referece spectrum measured")

        threading.Thread(target=worker, daemon=True).start()

    def show_max_val_pixel(self):
        max_pixel = np.argmax(self.cur_spectrum)
        messagebox.showinfo("Max Pixel", f"Maximum intensity at pixel {max_pixel}")

    # ------------------------------------------------------------------
    # Absorbance methods
    # ------------------------------------------------------------------

    def measure_absorbance_spectrum_click(self):
        if self.ref_spectrum is None:
            messagebox.showwarning("No reference", "Please measure a reference spectrum first.")
            return

        if self.dark_count_subtracted == False:
            proceed = messagebox.askokcancel("Dark count not subtracted", "Dark counts have not been subtracted. Do you want to continue?") 
            if not proceed:
                return

        if self.live_view_active:
            self.toggle_live_view()

        if self.spectrometer_busy:
            return

        self.spectrometer_busy = True
        self.toggle_spectrometer_buttons()

        def worker():
            try:
                self.set_status(f"Measuring absorbance spectrum...")
                self.spec.measure()
                self.sample_spectrum = self.spec.spectrum
                self.abs_spectrum = absorbance(self.ref_spectrum, self.sample_spectrum)
                self.cur_spectrum = self.abs_spectrum.copy()
                self.cur_spectrum_kind = "Absorbance"
                self.after(0, self.plot_absorbance_spectrum)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Measurement failed:\n{e}"))
            finally:
                self.set_status(f"Absorbance spectrum measured")
                self.spectrometer_busy = False
                self.after(0, self.toggle_spectrometer_buttons)

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # CD methods
    # ------------------------------------------------------------------

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
        self.set_status(f"Set CD settings")

    def measure_cd_reference_click(self):
        if self.motor_moving:
            return

        if self.dark_count_subtracted == False:
            proceed = messagebox.askokcancel("Dark count not subtracted", "Dark counts have not been subtracted. Do you want to continue?") 
            if not proceed:
                return

        if self.live_view_active:
            self.toggle_live_view()

        self.motor_moving = True
        self.toggle_motor_buttons()
        self.toggle_spectrometer_buttons()

        def worker():
            try:
                self.set_status("Homing motor before CD scan...")
                self.motor.home()
                self.set_status("CD reference scan (LHC)...")
                position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["LHC"], 360)
                self.motor.move(position, 60000)
                self.spec.measure()
                self.ref_lhc_intensities = self.spec.spectrum.copy()
                self.weak_signal_mask = (self.spec.spectrum < WEAK_SIGNAL_CUTOFF)

                self.set_status("CD reference scan (RHC)...")
                position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["RHC"], 360)
                self.motor.move(position, 60000)
                self.spec.measure()
                self.ref_rhc_intensities = self.spec.spectrum.copy()

                self.cd_ref_spectrum = delta_absorbance(self.ref_lhc_intensities, self.ref_rhc_intensities)
                self.cur_spectrum = self.cd_ref_spectrum.copy()
                self.cur_spectrum_kind = "CD Reference"

                self.set_status("CD scan complete.")
                self.after(0, self.plot_cd_reference)
            except Exception as e:
                self.set_status(f"CD scan failed: {e}")
            finally:
                self.motor_moving = False
                self.after(0, self.toggle_motor_buttons)
                self.after(0, self.toggle_spectrometer_buttons)
                self.cur_spectrum = self.cd_ref_spectrum

        threading.Thread(target=worker, daemon=True).start()
        
    def measure_cd_spectrum_click(self):
        if self.cd_ref_spectrum is None:
            messagebox.showwarning("No reference", "Please measure a CD reference spectrum first.")
            return

        if self.dark_count_subtracted == False:
            proceed = messagebox.askokcancel("Dark count not subtracted", "Dark counts have not been subtracted. Do you want to continue?") 
            if not proceed:
                return

        if self.live_view_active:
            self.toggle_live_view()
        
        if self.motor_moving:
            return

        self.motor_moving = True
        self.toggle_motor_buttons()
        self.toggle_spectrometer_buttons()

        def worker():
            try:
                self.set_status("Homing motor before CD scan...")
                self.motor.home()

                temp_lhc_intensities = np.zeros_like(self.spec.spectrum)
                temp_rhc_intensities = np.zeros_like(self.spec.spectrum)

                for i in range(self.cd_cycles):
                    self.set_status(f"CD scan: cycle {i + 1}/{self.cd_cycles} (LHC)...")
                    position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["LHC"], 360)
                    self.motor.move(position, 60000)
                    self.spec.measure()
                    temp_lhc_intensities = temp_lhc_intensities + self.spec.spectrum

                    self.set_status(f"CD scan: cycle {i + 1}/{self.cd_cycles} (RHC)...")
                    position = np.mod(OFFSET_FRESNEL_ANGLE + POL_DICT["RHC"], 360)
                    self.motor.move(position, 60000)
                    self.spec.measure()
                    self.rhc_intensities = self.spec.spectrum
                    temp_rhc_intensities = temp_rhc_intensities + self.spec.spectrum

                self.lhc_intensities = temp_lhc_intensities / self.cd_cycles
                self.rhc_intensities = temp_rhc_intensities / self.cd_cycles
                self.cd_spectrum = delta_absorbance(self.lhc_intensities, self.rhc_intensities) - self.cd_ref_spectrum
                self.cd_spectrum_millideg = ellipticity_millideg(self.lhc_intensities, self.rhc_intensities) - ellipticity_millideg(self.ref_lhc_intensities, self.ref_rhc_intensities)
                self.avg_abs_spectrum = avg_absorbance(
                    self.lhc_intensities,
                    self.rhc_intensities,
                    self.ref_lhc_intensities,
                    self.ref_rhc_intensities
                    )
                self.g_factor = g_factor(
                    self.lhc_intensities,
                    self.rhc_intensities,
                    self.ref_lhc_intensities,
                    self.ref_rhc_intensities
                    )
                
                self.cur_spectrum = self.cd_spectrum.copy()
                self.cur_spectrum_kind = "CD"

                self.after(0, self.plot_cd_spectrum)
                self.set_status("CD scan complete.")
            except Exception as e:
                self.set_status(f"CD scan failed: {e}")
            finally:
                self.motor_moving = False
                self.after(0, self.toggle_motor_buttons)
                self.after(0, self.toggle_spectrometer_buttons)
                self.cur_spectrum = self.cd_spectrum

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Plotting methods
    # ------------------------------------------------------------------

    def _plot_spectrum(
        self,
        data,
        title: str,
        ylabel: str,
        include_weak_signal: bool = True,
        ylim_mode: str = "auto",   # "auto" | "zero_lower" | "symmetric"
        ylim_max: float = 0.04,
        filename: str = False,
        show: bool = True,
    ):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.spec.wavelengths, data, color="#2563eb", linewidth=1.2)

        has_legend = False

        if include_weak_signal:
            ax.fill_between(
                self.spec.wavelengths, 0, 1,
                where=self.weak_signal_mask,
                color="#848282ff", alpha=0.5,
                label=f'Weak signal range (Counts < {WEAK_SIGNAL_CUTOFF})',
                transform=ax.get_xaxis_transform()
            )
            has_legend = True

        if self.spec.broken_wavelength_range is not None:
            ax.fill_between(
                self.spec.wavelengths, 0, 1,
                where=self.spec.broken_wavelength_mask,
                color="#ff3838", alpha=0.5,
                label='Malfunctioning pixel range',
                transform=ax.get_xaxis_transform()
            )
            has_legend = True

        if has_legend:
            ax.legend()

        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel("Wavelength (nm)", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)

        if ylim_mode == "zero_lower":
            ax.set_ybound(lower=0)
        elif ylim_mode == "symmetric":
            ylim = np.max([0.04, np.max(np.abs(data[~self.weak_signal_mask]))])
            ax.set_ylim([-ylim, ylim])
        # "auto" -> leave matplotlib's default limits

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

    def plot_absorbance_spectrum(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.abs_spectrum, "Measured absorbance spectrum", "Absorbance",
            ylim_mode="zero_lower", ylim_max=2, filename=filename, show=show,
        )

    def plot_cd_reference(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.cd_ref_spectrum, "Measured Circular Dichroism reference", "CD (absorbance)",
            ylim_mode="symmetric", ylim_max=0.04, filename=filename, show=show,
        )

    def plot_cd_spectrum(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.cd_spectrum, "Measured Circular Dichroism spectrum", "CD (absorbance)",
            ylim_mode="symmetric", ylim_max=0.04, filename=filename, show=show,
        )

    def plot_ellipticity_spectrum(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.cd_spectrum_millideg, "Measured Ellipticity spectrum", "Ellipticity (mdeg)",
            ylim_mode="symmetric", ylim_max=1000, filename=filename, show=show,
        )

    def plot_avg_absorbance(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.avg_abs_spectrum, "Measured absorbance spectrum", "Absorbance",
            ylim_mode="zero_lower", ylim_max=2, filename=filename, show=show,
        )

    def plot_g_factor(self, filename: str = False, show: bool = True):
        self._plot_spectrum(
            self.g_factor, "Measured g-factor", "g-factor",
            ylim_mode="symmetric", ylim_max=0.1, filename=filename, show=show,
        )

    # ------------------------------------------------------------------
    # Saving methods
    # ------------------------------------------------------------------

    def save_data_spectrum_click(self):
        name = self.filename_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a filename.")
            return

        if self.cur_spectrum is None or self.cur_spectrum_kind is None:
            messagebox.showwarning("Nothing to save", "No spectrum has been measured yet.")
            return

        out_dir = os.path.join(self.current_dir, "Outputs")
        os.makedirs(out_dir, exist_ok=True)
        filepath = os.path.join(out_dir, name + ".csv")

        if os.path.exists(filepath):
            if not messagebox.askyesno("File exists", f"{name}.csv already exists. Overwrite?"):
                return

        n = self.spec.DeviceInfo.nRealPixelNo
        wl = self.spec.wavelengths

        kind_config = {
            "Reference": (
                ["Index", "Wavelength", "Intensity", "Weak signal flag"],
                lambda j: [j + 1, wl[j], self.cur_spectrum[j], self.weak_signal_mask[j]],
            ),
            "Absorbance": (
                ["Index", "Wavelength", "Reference intensity", "Sample intensity", "Absorbance", "Weak signal flag"],
                lambda j: [j + 1, wl[j], self.ref_spectrum[j], self.sample_spectrum[j], self.abs_spectrum[j], self.weak_signal_mask[j]],
            ),
            "CD Reference": (
                ["Index", "Wavelength", "LHC intensity", "RHC intensity", "Delta absorbance", "Weak signal flag"],
                lambda j: [j + 1, wl[j], self.ref_lhc_intensities[j], self.ref_rhc_intensities[j], self.cd_ref_spectrum[j], self.weak_signal_mask[j]],
            ),
            "CD": (
                ["Index", "Wavelength", "LHC reference intensity", "RHC reference intensity",
                "LHC intensity", "RHC intensity", "Reference delta absorbance", "Delta absorbance",
                "Ellipticity", "g-factor", "Average absorbace", "Weak signal flag"],
                lambda j: [
                    j + 1, wl[j],
                    self.ref_lhc_intensities[j], self.ref_rhc_intensities[j],
                    self.lhc_intensities[j], self.rhc_intensities[j],
                    self.cd_ref_spectrum[j], self.cd_spectrum[j],
                    self.cd_spectrum_millideg[j], self.g_factor[j], self.avg_abs_spectrum[j], self.weak_signal_mask[j]
                ],
            ),
        }

        config = kind_config.get(self.cur_spectrum_kind)
        if config is None:
            messagebox.showerror("Error", "Error, spectrum kind not recognized.")
            return

        header, row_fn = config
        try:
            with open(filepath, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(header)
                for j in range(n):
                    writer.writerow(row_fn(j))
            self.set_status(f"Saved data to {name}.csv")
        except OSError as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def _get_plot_filename(self, suffix: str):
        """Validate the filename entry and return an 'Outputs/<name><suffix>' path (no extension)."""
        name = self.filename_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a filename.")
            return None

        out_dir = os.path.join(self.current_dir, "Outputs")
        os.makedirs(out_dir, exist_ok=True)
        return os.path.join("Outputs", name + suffix)

    def save_plot_ref_click(self):
        if self.ref_spectrum is None:
            messagebox.showwarning("No data", "Please measure a reference spectrum first.")
            return

        filename = self._get_plot_filename("_ref")
        if filename is None:
            return

        self._plot_spectrum(
            self.ref_spectrum, "Measured reference spectrum", "Intensity (counts)",
            ylim_mode="zero_lower", filename=filename, show=True,
        )
        self.set_status(f"Saved reference plot to {filename}.png")

    def save_plot_abs_click(self):
        if self.abs_spectrum is None:
            messagebox.showwarning("No data", "Please measure an absorbance spectrum first.")
            return

        filename = self._get_plot_filename("_abs")
        if filename is None:
            return

        self.plot_absorbance_spectrum(filename=filename, show=True)
        self.set_status(f"Saved absorbance plot to {filename}.png")

    def save_plot_avg_abs_click(self):
        if self.avg_abs_spectrum is None:
            messagebox.showwarning("No data", "Please measure an absorbance spectrum first.")
            return

        filename = self._get_plot_filename("_avg_abs")
        if filename is None:
            return

        self.plot_avg_absorbance(filename=filename, show=True)
        self.set_status(f"Saved average absorbance plot to {filename}.png")

    def save_plot_cd_ref_click(self):
        if self.cd_ref_spectrum is None:
            messagebox.showwarning("No data", "Please measure a CD reference spectrum first.")
            return

        filename = self._get_plot_filename("_cd_ref")
        if filename is None:
            return

        self.plot_cd_reference(filename=filename, show=True)
        self.set_status(f"Saved CD reference plot to {filename}.png")

    def save_plot_cd_click(self):
        if self.cd_spectrum is None:
            messagebox.showwarning("No data", "Please measure a CD spectrum first.")
            return

        filename = self._get_plot_filename("_cd")
        if filename is None:
            return

        self.plot_cd_spectrum(filename=filename, show=True)
        self.set_status(f"Saved CD plot to {filename}.png")

    def save_plot_ellipticity_click(self):
        if self.cd_spectrum_millideg is None:
            messagebox.showwarning("No data", "Please measure a CD spectrum first.")
            return

        filename = self._get_plot_filename("_ellipticity")
        if filename is None:
            return

        self.plot_ellipticity_spectrum(filename=filename, show=True)
        self.set_status(f"Saved ellipticity plot to {filename}.png")

    def save_plot_g_factor_click(self):
        if self.g_factor is None:
            messagebox.showwarning("No data", "Please measure a CD spectrum first.")
            return

        filename = self._get_plot_filename("_gfactor")
        if filename is None:
            return

        self.plot_g_factor(filename=filename, show=True)
        self.set_status(f"Saved g-factor plot to {filename}.png")

if __name__ == "__main__":
    app = ControlPanel()
    app.mainloop()