## Lab Report

### Monday 24/08/26

- 10:00 Tour Lab
- 11:30 Study components and install software
- 15:00 Make components list
- 15:30 Try to install Kinesis on CIC laptop, didn't work
- 17:30 Look in laser room for components
- 18:00 Test assembly

#### Notes

### Tuesday 25/08/26

- 9:00 3D print training
- 10:00 Try to install Kinesis on CIC laptop, works
- 11:00 Simple Python script to control motor
- 12:00 Fix spectrometer dlls
- 14:00 Design motor holder
- 15:30 Print holder motor

#### Notes
The provided SDK example for the spectrometer is not working, I had to replace the dll file with the one installed with the SM32pro software. Also the provided code had to be debugged. The dll is 32 bit, so we need to use 32 bit Python, for which Python 3.11.7 is best. We also need to install compatible numpy (1.26.4), kiwisolver (1.4.7) and matplotlib (3.7.5) versions.
