import tkinter as tk
import sys
import subprocess
import os
from SPdbUSBm import SPdbUSBm # SPdbUsbm dll
from tkinter import ttk, filedialog, messagebox
import ctypes
import time
import asyncio
import threading
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError:
    # Pinned to versions with prebuilt win32 wheels (matplotlib 3.8+ dropped win32 wheels,
    # and kiwisolver 1.5+ did too), so this installs cleanly on 32-bit Python without needing
    # a C/C++ compiler on the machine.
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "matplotlib==3.7.5", "numpy==1.26.4", "kiwisolver==1.4.7",
    ])
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np

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

class SDK_USBm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SDK USBm")
        self.geometry("620x650")
        self.pDeviceInfo = (DeviceInfo * 10)()
        self.currentCh = ctypes.c_short(-1)
        self.bExtTrigger = False
        self.is_updating = False  # Variable to track update state
        self.dCoefficient = (ctypes.c_double * 4)()
        self.dWL = None
        self.update_task = None  # Variable to store asynchronous task
        # Dictionary to track line visibility
        self.line_visibility = {"Reference": True, "Real-time": True}

        # Functions for using the DLL
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(self.current_dir, 'SPdbUSBm.dll')
        self.spdb = SPdbUSBm(dll_path)

        # Channel Configuration Group
        self.chn_config = tk.LabelFrame(self, text="Channel Configuration")
        self.chn_config.pack(padx=10, pady=10, fill="both")

        self.check_connections = tk.Button(self.chn_config, text="Check Connections", command=self.check_connections_click)
        self.check_connections.grid(row=0, column=0, padx=10, pady=5)

        self.check_con_text = tk.Entry(self.chn_config, state="readonly")
        self.check_con_text.grid(row=0, column=1, padx=10, pady=5, columnspan=3, sticky="ew")

        self.label_channel = tk.Label(self.chn_config, text="Channel #")
        self.label_channel.grid(row=1, column=0, padx=10, pady=5)

        self.cb_sel_channel = ttk.Combobox(self.chn_config, state="readonly")
        self.cb_sel_channel.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.cb_sel_channel.bind("<<ComboboxSelected>>", self.on_combobox_select)

        self.label_integration_time = tk.Label(self.chn_config, text="Integration Time:")
        self.label_integration_time.grid(row=2, column=0, padx=10, pady=5)

        self.n_int_time = tk.Spinbox(self.chn_config, from_=1, to=1000, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.n_int_time.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.n_int_time.delete(0, "end")  # Delete the existing value
        self.n_int_time.insert(0, 30)     # Insert the new value
       
        self.label_time_avg = tk.Label(self.chn_config, text="Time Average:")
        self.label_time_avg.grid(row=2, column=2, padx=10, pady=5)

        self.n_time_avg = tk.Spinbox(self.chn_config, from_=1, to=100 ,validate="key",validatecommand=(self.register(self.TimeAverage_TextChanged), "%P"))
        self.n_time_avg.grid(row=2, column=3, padx=10, pady=5, sticky="ew")


        # Wavelength Data Group
        self.gb_wl_data = tk.LabelFrame(self, text="Wavelength Data")
        self.gb_wl_data.pack(padx=10, pady=10, fill="both")
        self.wavelength = tk.IntVar()  # Variable for wavelength data radiobuttons
        self.rb_factory_data = tk.Radiobutton(self.gb_wl_data, text="Factory Default Data", value=0, variable=self.wavelength)
        self.rb_factory_data.pack(side="left", padx=10, pady=5)
        self.rb_user_data = tk.Radiobutton(self.gb_wl_data, text="User Calibration Data", value=1, variable=self.wavelength, command=self.wavelengthData_check)
        self.rb_user_data.pack(side="left", padx=10, pady=5)

        # Signal Processing Group
        self.group_box1 = tk.LabelFrame(self, text="Signal Processing")
        self.group_box1.pack(padx=10, pady=10, fill="both")

        self.baseline_var = tk.IntVar()
        self.offset_var = tk.IntVar()
        
        self.btn_read_dark = tk.Button(self.group_box1, text="Read Dark", state="disabled", command=self.read_dark_click)
        self.btn_read_dark.pack(side="left", padx=10, pady=5)
        
        self.chk_baseline_correction = tk.Checkbutton(self.group_box1, text="Baseline Correction", variable = self.baseline_var ,state="disabled", command=self.on_baseline_correction_checked)
        self.chk_baseline_correction.pack(side="left", padx=10, pady=5)
        
        self.chk_offset_correction = tk.Checkbutton(self.group_box1, text="Offset Correction", variable = self.offset_var ,state="disabled", command=self.on_offset_correction_checked)
        self.chk_offset_correction.pack(side="left", padx=10, pady=5)

        self.autodark_value = tk.IntVar()

        self.top_frame = tk.Frame(self)
        self.top_frame.pack(padx=10, pady=10, fill="x")  # Use the full X-axis range

        self.AutoDark = tk.LabelFrame(self.top_frame, text = "Auto Dark")
        self.AutoDark.pack(side = "left",padx=5, pady=5, fill= "y")

        self.autodark_check = tk.Checkbutton(self.AutoDark, text = "Auto Dark", variable = self.autodark_value)
        self.autodark_check.grid(row=0,column=0,pady=5,sticky="w")

        self.shutter_frame = tk.LabelFrame(self.top_frame, text="Shutter Control")
        self.shutter_frame.pack(side = "left",padx=5, pady=5, fill="y", expand=True)

        self.btn_Shutter_On = tk.Button(self.shutter_frame, text="shutter Open", command=lambda: self.on_Shutter_click(1),width=10)
        self.btn_Shutter_On.grid(row=0, column=0, columnspan=1, padx=20, pady=5, sticky="e")

        self.btn_Shutter_OFF = tk.Button(self.shutter_frame, text="shutter Close", command=lambda: self.on_Shutter_click(0),width=10)
        self.btn_Shutter_OFF.grid(row=0, column=1, columnspan=2, padx=20, pady=5, sticky="e")

        self.Shutter_state_label = tk.Label(self.shutter_frame, text="Shutter State: Unknown", relief="sunken", bd=2)
        self.Shutter_state_label.grid(row=0, column=4, columnspan=3, padx=15, pady=5, sticky="ew")

        # Triggering Mode Group
        self.group_box2 = tk.LabelFrame(self, text="Triggering Mode")
        self.group_box2.pack(padx=10, pady=10, fill="both")
        
        self.trigger = tk.IntVar()  # Variable for triggering mode radiobuttons

        # Using grid for layout
        self.rb_free_run_prev = tk.Radiobutton(self.group_box2, text="Free Run Previous", value=1, variable=self.trigger)
        self.rb_free_run_prev.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.rb_free_run_next = tk.Radiobutton(self.group_box2, text="Free Run Next", value=2, variable=self.trigger)
        self.rb_free_run_next.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        self.rb_external_trg_falling = tk.Radiobutton(self.group_box2, text="External Trigger(Falling Edge)", value=3, variable=self.trigger)
        self.rb_external_trg_falling.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.rb_external_trg_rising = tk.Radiobutton(self.group_box2, text="External Trigger(Rising Edge)", value=4, variable=self.trigger)
        self.rb_external_trg_rising.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.rb_sw_trigger = tk.Radiobutton(self.group_box2, text="S/W Trigger", value=0, variable=self.trigger)
        self.rb_sw_trigger.grid(row=2, column=0, padx=10, pady=5, sticky="w", columnspan=2)
        
        self.btn_trigger_mode = tk.Button(self.group_box2, text="Set", command=self.trigger_mode_click,width=10)
        self.btn_trigger_mode.grid(row=2, column=1, columnspan=2, padx=20, pady=5, sticky="e")


        

        # Data Acquisition Group
        self.data_acq = tk.LabelFrame(self, text="Data Acquisition")
        self.data_acq.pack(padx=10, pady=10, fill="both")
        
        self.label_save_file = tk.Label(self.data_acq, text="Save File Name:")
        self.label_save_file.grid(row=0, column=0, padx=10, pady=5)
        
        self.save_file_name = tk.Entry(self.data_acq)
        self.save_file_name.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.save_file_name.insert(0,"test")

        #self.outputTrigger = tk.Checkbutton(self.data_acq, text="Output Trigger")
        #self.outputTrigger.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.get_data_all = tk.Button(self.data_acq, text="Get Data And Save", command=self.get_data_all_click)
        self.get_data_all.grid(row=2, column=0, padx=10, pady=5)
        
        self.graph = tk.Button(self.data_acq, text="View Data On a Graph", command=self.graph_click)
        self.graph.grid(row=2, column=1, padx=10, pady=5)
        
        self.close = tk.Button(self.data_acq, text="Close", command=self.close_click)
        self.close.grid(row=2, column=2, padx=10, pady=5)

        self.check_connections_click()


    def _validate(self, P):
        if self.currentCh.value >= 0:
            if P.isdigit():
                self.pDeviceInfo[self.currentCh.value].lIntTime = (int)(P)
                sRtn = self.spdb.spSetIntEx(self.pDeviceInfo[self.currentCh.value].lIntTime, self.currentCh)
        return P.isdigit() or P == ""
        # Add device
    def check_connections_click(self):
        self.check_con_text.config(state="normal")
        sRtn = self.spdb.spTestAllChannels(0)
        self.cb_sel_channel['values'] = ()
        current_values = list(self.cb_sel_channel['values'])
        if sRtn > 0:
            sTotChnlNum = sRtn;
            self.check_con_text.insert(0,"Testing the USB borad... OK!  Dev Num : " + str(sTotChnlNum))
            self.pDeviceInfo = (DeviceInfo * sTotChnlNum)()
            sRtn = self.spdb.spSetupAllChannels()
            for i in range(sTotChnlNum):    
                model_buffer = ctypes.create_string_buffer(256)
                serial_buffer = ctypes.create_string_buffer(256)
                sRtn = self.spdb.spDevInfo(model_buffer, serial_buffer, ctypes.c_short(i))
                self.pDeviceInfo[i].Model = model_buffer.value.decode('utf-8')
                self.pDeviceInfo[i].Serial = serial_buffer.value.decode('utf-8')
                # Format the new item to be added
                new_item = f"Ch#{i}: {self.pDeviceInfo[i].Model.strip()} - {self.pDeviceInfo[i].Serial.strip()}"
                # Add formatted items to the list.
                current_values.append(new_item)
                self.device_setup(self.pDeviceInfo[i].Model.strip(), i)

                # Additional settings based on the device model
                if self.pDeviceInfo[i].Model.strip() == "SM304":
                    sRtn = self.spdb.spSetTEC(ctypes.c_short(1), ctypes.c_short(i))
                    if sRtn < 0:
                        raise Exception(f"spSetTEC Error for channel {i}")

                    sRtn = self.spdb.spSelectCF(ctypes.c_short(1), ctypes.c_short(i))
                    if sRtn < 0:
                        raise Exception(f"spSelectCF Error for channel {i}")

                if self.spdb.spGetDevIsNew(ctypes.c_short(i)) == 1:
                    self.spdb.spSetIntMode(ctypes.c_short(0), self.pDeviceInfo[i].lIntTime, ctypes.c_short(i))
                    # Change the state of the rbSWTrigger checkbox
                    self.rb_sw_trigger.select()
                else:
                    self.spdb.spSetTrgEx(ctypes.c_short(11), ctypes.c_short(i))
                    # Change the state of the rbFreeRunPrev checkbox
                    self.rb_free_run_prev.select()



                self.currentCh = ctypes.c_short(0)
                self.check_con_text.config(state="disabled")
                self.cb_sel_channel['values'] = current_values
                if current_values:  # If current_values is not empty
                    sRtn = self.spdb.spIntShutter(0)
                    if sRtn == 1:
                        rtn = self.spdb.spGetShutter(0)
                        if rtn == 1:
                            self.Shutter_state_label.config(text="Shutter State: Open", bg="lightgreen") # Status Update
                        else:
                            self.Shutter_state_label.config(text="Shutter State: Close", bg="lightgreen") # Status Update
                    else :
                        self.Shutter_state_label.config(text="Shutter State: None", bg="lightgreen") # Status Update
                    self.cb_sel_channel.current(0)

                if self.pDeviceInfo[self.currentCh.value].Model == "SM304":
                    self.btn_read_dark.config(state="normal")
                    self.chk_baseline_correction.config(state="normal")
                    self.chk_offset_correction.config(state="normal")

    def wavelengthData_check(self):
        if self.wavelength.get() == 1:  # User calibration data
            dWaveLength = (ctypes.c_double * 12)()
            dPixelNo = (ctypes.c_double * 12)()
            dWaveLength_values  = [253.7, 313.2, 365.0, 404.7, 435.8, 546.1, 577.0, 579.1, 696.5, 763.5, 811.5, 912.3]
            dPixelNo_values  = [348, 465, 567, 643, 703, 910, 967, 971, 1186, 1306, 1392, 1570]
            for i in range(12):
                dWaveLength[i] = dWaveLength_values[i]
                dPixelNo[i] = dPixelNo_values[i]
            self.spdb.spPolyFit(dPixelNo,dWaveLength,12,self.dCoefficient,3)
            getDevInfo = self.pDeviceInfo[self.currentCh.value]
            self.dWL = (ctypes.c_double * getDevInfo.nRealPixelNo)()
            for j in range(getDevInfo.nRealPixelNo):
                self.spdb.spPolyCalc(self.dCoefficient, 3, j+1, dWaveLength);
                self.dWL[j] = dWaveLength[0] 
        pass

        # device Setup
    def device_setup(self, model, channel):
        if "SM24" in model:
            self.pDeviceInfo[channel].nTOTPixelNo = 2080
            self.pDeviceInfo[channel].nRealPixelNo = 2048
            self.pDeviceInfo[channel].EffectivePixelIndex = 32
            self.pDeviceInfo[channel].CCDType = ctypes.c_short(0)  # Assume SP_CCD_SONY is 0
        elif "SM44" in model:
            self.pDeviceInfo[channel].nTOTPixelNo = 3680
            self.pDeviceInfo[channel].nRealPixelNo = 3648
            self.pDeviceInfo[channel].EffectivePixelIndex = 32
            self.pDeviceInfo[channel].CCDType =  ctypes.c_short(1)  # Assume SP_CCD_TOSHIBA is 1
        elif "SM303" in model:
            self.pDeviceInfo[channel].nTOTPixelNo = 1056
            self.pDeviceInfo[channel].nRealPixelNo = 1024
            self.pDeviceInfo[channel].EffectivePixelIndex = 10
            self.pDeviceInfo[channel].CCDType =  ctypes.c_short(2)  # Assume SP_CCD_PDA is 2
        elif "SM304" in model:
            self.pDeviceInfo[channel].nTOTPixelNo = 512
            self.pDeviceInfo[channel].nRealPixelNo = 512
            self.pDeviceInfo[channel].EffectivePixelIndex = 0
            self.pDeviceInfo[channel].CCDType =  ctypes.c_short(3)  # Assume SP_CCD_G9212 is 3
        elif "SM642" in model:
            self.pDeviceInfo[channel].nTOTPixelNo = 2080
            self.pDeviceInfo[channel].nRealPixelNo = 2048
            self.pDeviceInfo[channel].EffectivePixelIndex = 10
            self.pDeviceInfo[channel].CCDType =  ctypes.c_short(4)  # Assume SP_CCD_S10420 is 4

        self.pDeviceInfo[channel].USBSpeed = ctypes.c_short(2)
        self.pDeviceInfo[channel].lIntTime = ctypes.c_long(30)
        self.pDeviceInfo[channel].lTimeAvg = ctypes.c_int(1)

        # Call the DLL function
        sRtn = self.spdb.spInitGivenChannel(self.pDeviceInfo[channel].CCDType,  ctypes.c_short(channel))
        if sRtn < 0:
            raise Exception(f"spInitGivenChannel Error for channel {channel}")
        return sRtn

    def on_combobox_select(self,event):
        selected_index = self.cb_sel_channel.current()  # Index of the selected channel
        self.currentCh = ctypes.c_short(selected_index)
        self.wavelengthData_check()

        sRtn = self.spdb.spIntShutter(selected_index)
        if sRtn == 1:
            rtn = self.spdb.spGetShutter(selected_index)
            if rtn == 1:
                self.Shutter_state_label.config(text="Shutter State: Open", bg="lightgreen") # Status Update
            else:
                self.Shutter_state_label.config(text="Shutter State: Close", bg="lightgreen") # Status Update
        else :
            self.Shutter_state_label.config(text="Shutter State: None", bg="lightgreen") # Status Update

        if self.pDeviceInfo[self.currentCh.value].Model== "SM304":
            self.btn_read_dark.config(state = "normal")
            self.chk_baseline_correction.config(state = "normal")
            self.chk_offset_correction.config(state = "normal")

    # Save data
    def get_data_all_click(self):
        # Call the spReadDataEx function
        channel = 0
        getDevInfo = self.pDeviceInfo[self.currentCh.value]

        # Allocate arrays
        DataArray = (ctypes.c_long * getDevInfo.nTOTPixelNo)()
        WLTableArray = (ctypes.c_double * getDevInfo.nRealPixelNo)()
        tempArray = (ctypes.c_long * getDevInfo.nTOTPixelNo)()
        
        # File path and header
        savePath = os.path.join(self.current_dir, self.save_file_name.get() + ".txt")
        header = "Index\tWavelength(nm)\t\tIntensity\n"
    
        # Write header to file
        with open(savePath, "w") as file:
            file.write(header)

        # Get wavelength table
        sRtn = self.spdb.spGetWLTable(WLTableArray, self.currentCh)
        if sRtn < 0:
            messagebox.showerror("Error", "Error in spGetWLTable")
            return

        # Data acquisition based on trigger mode
        if not self.bExtTrigger:  # Internal trigger mode
            for _ in range(getDevInfo.lTimeAvg):
                sRtn = self.spdb.spReadDataEx(DataArray, self.currentCh)
                if sRtn < 0:
                    messagebox.showerror("Error", "Error in spReadDataEx")
                    return
                for j in range(getDevInfo.nRealPixelNo):
                    if self.autodark_value.get() == 1:
                        pass
                    tempArray[j + getDevInfo.EffectivePixelIndex] += DataArray[j + getDevInfo.EffectivePixelIndex]
        else:  # External trigger mode
            for _ in range(getDevInfo.lTimeAvg):
                while True:
                    sRtn = self.spdb.spReadDataEx(DataArray, self.currentCh)
                    if sRtn != -99:
                        break
                for j in range(getDevInfo.nRealPixelNo):
                    tempArray[j + getDevInfo.EffectivePixelIndex] += DataArray[j + getDevInfo.EffectivePixelIndex]

                            # Average the data
        if getDevInfo.lTimeAvg == 1:
            pass
        else:
            for j in range(getDevInfo.nRealPixelNo):
                DataArray[j + getDevInfo.EffectivePixelIndex] = int(tempArray[j + getDevInfo.EffectivePixelIndex] / getDevInfo.lTimeAvg + 0.5)

        # Save data to file
        with open(savePath, "a") as file:
            if self.wavelength.get() == 1:  # User calibration data
                for j in range(getDevInfo.nRealPixelNo):
                    file.write(f"{j + 1}\t{self.dWL[j]:.4f}\t\t{DataArray[j + getDevInfo.EffectivePixelIndex]:.4f}\n")
            else:  # Factory default data
                for j in range(getDevInfo.nRealPixelNo):
                    file.write(f"{j + 1}\t{WLTableArray[j]:.4f}\t\t{DataArray[j + getDevInfo.EffectivePixelIndex]:.4f}\n")

    # graph draw
    def graph_click(self):
        graph_window = self.create_graph_window()

        fig, ax = plt.subplots(figsize=(10, 6))
        self.update_graph(fig, ax)

        self.add_canvas_to_window(graph_window, fig)
        self.add_buttons_to_window(graph_window, fig, ax)

    def create_graph_window(self):
        graph_window = tk.Toplevel(self)
        graph_window.title("Wavelength Intensity")
        return graph_window

    # Retrieve data for the graph
    def get_graph_data(self):
        getDevInfo = self.pDeviceInfo[self.currentCh.value]
        WLTableArray = (ctypes.c_double * getDevInfo.nRealPixelNo)()
        DataArray = (ctypes.c_long * getDevInfo.nTOTPixelNo)()
        tempArray = (ctypes.c_long * getDevInfo.nTOTPixelNo)()

        if self.wavelength.get() == 1:  # User calibration data
            WLTableArray = self.dWL
        else:
            sRtn = self.spdb.spGetWLTable(WLTableArray, self.currentCh)
            if sRtn < 0:
                messagebox.showerror("Error", "Error in spGetWLTable")
                return None, None
            
        if not self.bExtTrigger:  # Internal trigger mode
            for _ in range(getDevInfo.lTimeAvg):
                sRtn = self.spdb.spReadDataEx(DataArray, self.currentCh)
                if sRtn < 0:
                    messagebox.showerror("Error", "Error in spReadDataEx")
                    return
                for j in range(getDevInfo.nRealPixelNo):
                    if self.autodark_value.get() == 1:
                        pass
                    tempArray[j + getDevInfo.EffectivePixelIndex] += DataArray[j + getDevInfo.EffectivePixelIndex]
        else:  # External trigger mode
            for _ in range(getDevInfo.lTimeAvg):
                while True:
                    sRtn = self.spdb.spReadDataEx(DataArray, self.currentCh)
                    if sRtn != -99:
                        break
                for j in range(getDevInfo.nRealPixelNo):
                    tempArray[j + getDevInfo.EffectivePixelIndex] += DataArray[j + getDevInfo.EffectivePixelIndex]

        if getDevInfo.lTimeAvg == 1:
            pass
        else:
            for j in range(getDevInfo.nRealPixelNo):
                DataArray[j + getDevInfo.EffectivePixelIndex] = int(tempArray[j + getDevInfo.EffectivePixelIndex] / getDevInfo.lTimeAvg + 0.5)

        wavelengths = np.array(WLTableArray[:getDevInfo.nRealPixelNo])
        intensities = np.array(DataArray[getDevInfo.EffectivePixelIndex:getDevInfo.EffectivePixelIndex + getDevInfo.nRealPixelNo])

        if self.autodark_value.get() == 1:
            intensities = self.auto_dark_correction(wavelengths, intensities)
        return wavelengths, intensities

    # Update graph data
    def update_graph(self, fig, ax):
        wavelengths, intensities = self.get_graph_data()  # Retrieve data
        if wavelengths is None or intensities is None:
            return

        ax.clear()  # Clear previous data
        real_time_line, = ax.plot(wavelengths, intensities, label="Real-time", picker=True)
        real_time_line.set_visible(self.line_visibility["Real-time"])  # Maintain previous visibility state
        ax.set_title("Wavelength Intensity")
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Intensity")
        ax.grid(True)
        ax.legend()

        lines = [real_time_line, real_time_line]
        leg = ax.legend()
        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(True)
            legline.set_pickradius(5)  # Set pick radius for easier clicking
            legline.set_gid(origline)

        fig.canvas.mpl_connect('pick_event', self.on_pick)

        fig.canvas.draw()  # Redraw the graph+

    # Legend event
    def on_pick(self, event):
        legline = event.artist
        origline = legline.get_gid()
        visible = not origline.get_visible()
        origline.set_visible(visible)
        legline.set_alpha(1.0 if visible else 0.2)  # Dim the legend when the graph is not visible
        self.line_visibility[origline.get_label()] = visible  # Save visibility state
        event.canvas.draw()

    # Open a new window for the graph
    def add_canvas_to_window(self, graph_window, fig):
        self.is_updating = False
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Add buttons to the graph window
    def add_buttons_to_window(self, graph_window, fig, ax):
        button_frame = tk.Frame(graph_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        start_button = tk.Button(button_frame, text="Start", command=lambda: self.start_updating(fig, ax))
        start_button.pack(side=tk.LEFT, padx=10, pady=10)

        stop_button = tk.Button(button_frame, text="Stop", command=self.stop_updating)
        stop_button.pack(side=tk.LEFT, padx=10, pady=10)

        save_button = tk.Button(button_frame, text="Save Graph", command=lambda: self.save_graph(fig))
        save_button.pack(side=tk.LEFT, padx=10, pady=10)

        close_button = tk.Button(button_frame, text="Close", command=graph_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # Start updating the graph
    def start_updating(self, fig, ax):
        if not self.is_updating:  # Prevent duplicate execution if already updating
            self.is_updating = True
            loop = asyncio.get_event_loop()
            self.update_task = loop.run_in_executor(None, self.run_update_graph, fig, ax)

    def run_update_graph(self, fig, ax):
        asyncio.run(self.update_graph_continuously(fig, ax))

    def auto_dark_correction(self, wavelengths, intensities):
        # Estimate dark noise: consider the average of the lowest intensity values as dark noise
        # Here, we treat values near the minimum as dark
        dark_threshold = np.percentile(intensities, 5)  # Estimate dark from the lowest 5%
        dark_noise = np.mean(intensities[intensities <= dark_threshold])

        # Subtract dark noise (ensure intensities do not become negative)
        corrected_intensities = intensities - dark_noise
        corrected_intensities = np.maximum(corrected_intensities, 0)  # Remove negative values

        return corrected_intensities

    # Stop updating the graph
    def stop_updating(self):
        if self.update_task is not None:
            self.update_task.cancel()  # Cancel asynchronous task
            self.update_task = None
        self.is_updating = False  # Set update state to False to stop

    # Update loop
    async def update_graph_continuously(self, fig, ax):
        while self.is_updating:
            start_time = time.time()  # Record start time
            self.update_graph(fig, ax)
            elapsed_time = time.time() - start_time  # Calculate time taken to retrieve data
            await asyncio.sleep(0)  # Wait asynchronously

    # Save the updated image
    def save_graph(self, fig):
        save_path = tk.filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if save_path:
            fig.savefig(save_path)

    # Close the window
    def close_click(self):
        self.stop_updating()
        self.destroy()

    # Read dark noise
    def read_dark_click(self):
        IDarkData = (ctypes.c_int * self.pDeviceInfo[self.currentCh.value].nTOTPixelNo)()
        sRtn = self.spdb.spReadDark(IDarkData, self.pDeviceInfo[self.currentCh.value].lTimeAvg, self.currentCh)
        if sRtn < 0:
            messagebox.showerror("Error", f"spReadDark Error")

    # Trigger Mode Change
    def trigger_mode_click(self):
        sDevVersion = self.spdb.spGetDevIsNew(self.currentCh.value)
        getDevInfo = self.pDeviceInfo[self.currentCh.value]
        self.bExtTrigger = False

        if sDevVersion == 1:
            if self.trigger.get() == 1:
                 self.spdb.spSetIntMode(self.trigger.get(),getDevInfo.lIntTime,self.currentCh.value)
            elif self.trigger.get() == 2:
                self.spdb.spSetIntMode(self.trigger.get(),getDevInfo.lIntTime,self.currentCh.value)
            elif self.trigger.get() == 0:
                self.spdb.spSetIntMode(self.trigger.get(),getDevInfo.lIntTime,self.currentCh.value)
            elif self.trigger.get() == 3:
                self.bExtTrigger = True
                self.spdb.spSetExtEdgeMode(0,self.currentCh.value)
            else :
                self.bExtTrigger = True
                self.spdb.spSetExtEdgeMode(1,self.currentCh.value)
        else :
            if self.trigger.get() == 1:
                self.spdb.spSetTrgEx(11,self.currentCh.value)
            elif self.trigger.get() == 2 or self.trigger.get() == 0:
                messagebox.showerror("Error", f"The device of USB Port #{self.currentCh.value} does not support")
            elif self.trigger.get() == 3:
                self.bExtTrigger = True
                self.spdb.spSetExtEdgeMode(0,self.currentCh.value)
            else :
                messagebox.showerror("Error", f"The device of USB Port #{self.currentCh.value} does not support")
        pass

    def TimeAverage_TextChanged(self, P):
        if self.currentCh.value >= 0:
            if P.isdigit():
                self.pDeviceInfo[self.currentCh.value].lTimeAvg = (int)(P)
        return P.isdigit() or P == ""

    def on_Shutter_click(self, P):
        sRtn = self.spdb.spShutter(P,self.currentCh.value)
        if sRtn < 0:
            messagebox.showerror("Error", f"Shutter Error")

        if P == 1:
            self.Shutter_state_label.config(text="Shutter State: Open", bg="lightgreen") # Status Update
        else :
            self.Shutter_state_label.config(text="Shutter State: Close", bg="lightgreen") # Status Update

    def on_GetShutter_click(self):
        sRtn = self.spdb.spGetShutter(self.currentCh.value)
        if sRtn < 0:
            messagebox.showerror("Error", f"Shutter Error")

        if sRtn == 1:
            self.Shutter_state_label.config(text="Shutter State: OPEN", bg="lightgreen") # Status Update
        else :
            self.Shutter_state_label.config(text="Shutter State: OFF", bg="lightgreen") # Status Update

    def on_baseline_correction_checked(self):
        # Check the checkbox status and control the device
        is_checked = self.baseline_var.get()
        s_checked = ctypes.c_short(1 if is_checked else 0)
        s_offset = ctypes.c_short(2000)
        d_gain = ctypes.c_double(1.5)
        

        sRtn = self.spdb.spSetBaseLineCorrection(s_checked, s_offset, d_gain, self.currentCh)
        if sRtn < 0:
            messagebox.showerror("Error", f"spSetBaseLineCorrection Error")

    def on_offset_correction_checked(self):
        # Check the checkbox status and control the device
        is_checked = self.offset_var.get()

        s_checked = ctypes.c_short(1 if is_checked else 0)

        sRtn = self.spdb.spSetOffsetCorrection(s_checked,self.currentCh)
        if sRtn < 0:
            messagebox.showerror("Error", f"spSetOffsetCorrection Error")

if __name__ == "__main__":
    app = SDK_USBm()
    app.mainloop()