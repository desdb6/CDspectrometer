"""
Class to control K10CR2 Thorlabs motor
Author: Des De Borger
Last modified: 25/08/2026
"""

import clr 
import time 

# Write in file paths of dlls needed. 
clr.AddReference("C:\\Program Files (x86)\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files (x86)\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files (x86)\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.IntegratedStepperMotorsCLI.dll")

# Import functions from dlls. 
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.IntegratedStepperMotorsCLI import *
from System import Decimal 

class K10CR2():
    def __init__(self, serial_number: str):
        try:
            # Build device list.  
            DeviceManagerCLI.BuildDeviceList()

            # create new device.
            self.serial_number = serial_number  # Replace this line with your device's serial number.
            self.device = CageRotator.CreateCageRotator(self.serial_number)
            
            # Connect to device. 
            self.device.Connect(self.serial_number)

            # Ensure that the device settings have been initialized.
            if not self.device.IsSettingsInitialized():
                self.device.WaitForSettingsInitialized(10000)  # 10 second timeout.
                assert self.device.IsSettingsInitialized() is True

            # Start polling loop and enable device.
            self.device.StartPolling(250)  #250ms polling rate.
            time.sleep(0.25)
            self.device.EnableDevice()
            time.sleep(0.25)  # Wait for device to enable.

            # Get Device Information and display description.
            device_info = self.device.GetDeviceInfo()
            print("Device connected succesfully:")
            print(device_info.Description)
    
            # Load any configuration settings needed by the controller/stage.
            motor_config = self.device.LoadMotorConfiguration(serial_number, DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

        except Exception as e:
                print(e)

    def move(self, pos : float, t : float):
        pos_dec = Decimal(pos)
        self.device.MoveTo(pos_dec, t)

    def home(self):
        self.device.Home(60000)

    def disconnect(self):
        self.device.StopPolling()
        self.device.Disconnect()

if __name__ == "__main__":
    motor = K10CR2(serial_number="55547014")
    print("\nHoming")
    motor.home()
    print("Moving to +45 degrees, LCPL")
    motor.move(45, 60000)
    print("Collecting intensity spectrum")
    time.sleep(6)
    print("Moving to -45 degrees, RCPL")
    motor.move(135, 60000)
    print("Collecting intensity spectrum")
    time.sleep(6)
    print("Done")
    motor.home()