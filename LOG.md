## Lab Report

### Monday 24/08/26

- 10:00 Visit: Tour Lab
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
- 17:00 Work on spectral composition simulation

#### Notes

##### SDK software

The provided SDK example for the spectrometer is not working, I had to replace the dll file with the one installed with the SM32pro software. Also the provided code had to be debugged. The dll is 32 bit, so we need to use 32 bit Python, for which Python 3.11.7 is best. We also need to install compatible numpy (1.26.4), kiwisolver (1.4.7) and matplotlib (3.7.5) versions.

##### Spectral composition simulation

Spectral composition simulation is best done with Mueller calculus/matrices. There is no intensity graph for the light source, so model as a blackbody curve?

### Wednesday 26/08/2026

- 9:00 Design motor holder v2
- 11:30 Print motor holder v2
- 12:00 Read spectrometer software manual
- 13:00 Visit: Laser scattering experiment to determine particle population size via Brownian motion
- 14:00 Design cuvette holder
- 16:00 Write code to control spectrometer  
- 17:00 Work on spectral composition simulation

#### Notes

##### 3D printer holder

I have removed one of the walls as it was not actually supporting the motor.
  
#### Spectrometer software

It needs a light source pointed directly into the fiber, otherwise it is just random noise and increasing the integration time does nothing.


### Thursday 27/08/2026

- 9:00 Book 3D printer
- 9:10 Figure out spectrometer code example
- 10:15 Print cuvette holder
- 10:30 Continue spectrometer code example study
- 11:30 Visit: Laser scattering experiment to determine particle population size via Brownian motion
- 11:45 Continue spectrometer code example study
- 12:30 Write my own spectrometer control script
- 13:30 Assemble cuvette holder
- 14:45 Design cuvette holder second version
- 15:00 Print cuvette holder second version
- 15:15 Improve spectrometer control code
- 17:00 Assemble setup with new cuvette holder

#### Notes

### Friday 28/08/2026
- 9:00 Design flex collimator holder
- 10:00 Print flex collimator holder
- 10:30 Print flex collimator holder second version
- 11:00 Print flex cuvette holder
- 11:30 Design flex collimator holder on baseplate
- 12:00 Visit: Bio 3D printer

#### Notes

### Monday 31/08/2026
- 9:00 Design stronger cuvette holder
- 9:30 Print stronger cuvette holder
- 10:00 Meeting Luis
- 10:20 Brainstorm calibration ideas

#### Notes

##### Brainstorm what to do until light source arrives
- Calibration can be done using the Jasco CD: open the shutter and select a wavelength, then put fiber in front of beam and record a spectrum -> fit a cubic polynomial through data points
- Characterize linear polarizer and find fast axis angle using other linear polarizers
- Look at beam shape by using a second fiber and shining flash light through it before the motor
- Design an enclosure for setup in suitable material, Bionanoplasmonics has its own filaments but check with Gerard as well
- Also for cuvette holder, study what material is best (this part probably needs to be reprinted once we know the beam shape)
- Do a measurement at the Jasco CD to see how it is done
