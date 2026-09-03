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
- 11:00 Research printing material
- 12:00 Visit: CD spectrometer
- 13:30 Look at beam size
- 14:30 Make calibration code
- 15:00 Get calibration data from CD
- 16:00 Research enclosure
- 17:00 Design enclosure fit test print

#### Notes

##### Brainstorm what to do until light source arrives
- Calibration can be done using the Jasco CD: open the shutter and select a wavelength, then put fiber in front of beam and record a spectrum -> fit a cubic polynomial through data points
- Characterize linear polarizer and find fast axis angle using other linear polarizers
- Look at beam shape by using a second fiber and shining flash light through it before the motor
- Design an enclosure for setup in suitable material, Bionanoplasmonics has its own filaments but check with Gerard as well
- Also for cuvette holder, study what material is best (this part probably needs to be reprinted once we know the beam shape)
- Do a measurement at the Jasco CD to see how it is done

##### Optical parts 3D printing
The 3D prints ideally have to be 100% opaque. Usually, a matte black PLA is opaque enough for optical setups, there is black matte TPLA in the print room. If there is still too much scattering, options include:
- Using a specialized opaque PLA, but shipping is expensive + takes time
- Cover parts in candle soot
- Use black paper to block out light
- Use paint/spray to finish prints
- Optimize infill patterns for internal reflections

Useful blog post checking filament opacity: https://www.thingiverse.com/groups/3dp-photo/forums/general/topic:7227#google_vignette

Paper on print material opacity characterization: https://pmc.ncbi.nlm.nih.gov/articles/PMC8208549/

Github for open source optical microscope, simply uses matte black PLA: https://github.com/TadPath/PUMA

##### Open source optomechanical 3D prints
https://osf.io/9kt52/overview

https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0059840

##### CCD photospectrometer calibration
We did this by basically using the Jasco CD as a monochromator, shining 10nm bandwidth light into the CCD fiber and noting the most intense pixel. The converstion from pixels to wavelengths is then done by fitting a cubic polynomial through the datapoints. The results show that the calibration hard coded into the SP python example is very wrong, and most likely not meant to be used for the SM440 photospectrometer; good that we checked this :)

### Tuesday 01/09/2026
- 9:00 Figure out time integration units
- 10:30 Print enclosure outline
- 11:15 Code live view and improve control panel buttons
- 12:30 Design enclosure fit test print second version
- 13:00 Light source arrived
- 13:30 Assembling setup
- 13:45 Testing spectrum measurements
- 15:00 Designing fast axis alignment experiment
- 17:00 Design collimator mount for light source
- 17:30 Look in LASER room for filters for fast axis alignment experiment

#### Notes

##### SP time integration units
I wrote a script to see what the conversion unit is between the inputted int time number and real time, as I couldn't make sense of it. The documentation said it is 10/3 us/count, but my script (time_int_testing.py) gives something very close to 50 us / count. I have built this into the spectrometer control script.


##### CCD dead pixel arrays
When testing the Tungsten light source, I noticed the spectrum shows a sharp dip at the same place every time, even without atmospheric interference. When shining a flash light we can see the same dip but smaller. My guess is that there are a few pixel rows with a worse quantum efficiency, or there is some other problem preventing these pixels from functioning correctly. Specifically, pixels 2046-2078 have this problem, corresponding to a spectral range of ~728nm-738nm.

##### Alignment experiment setup
We have to align the setup in at least two ways:
1. Rotation around the beam axis
2. Angle of incidence (has to be perpendicular to the surface of the optomechanical component)

Rotation around the beam axis: The fresnel rhomb retarder is difficult to align as it is not placed on a rotating mount. I think it is more practical to leave the fresnel rhomb retarder at an arbitrary angle (but near vertical), and to align the linear polariser on the motorized mount, which can be very accurately moved. We need to design an experiment where it is possible to find a maximum\minimum by changing only **one** setting (preferable the motor position).

I worked out the Mueller calculus and found a protocol that would work. We would put a second linear polariser behind the fresnel rhomb, work in the reference frame of the fast axis of the second polariser and define the angles $$\phi$$ and $$\theta$$ as the angles between the fast axes of the first linear polariser and fresnel rhomb respectively. The transmitted intensity for an unpolarised beam is then 

$$I(\theta, \phi) \propto \cos(2\theta)\cos(2(\theta-\phi))$$

We will align the two polarisers perpendicular to make the first cosine as big as possible to see big changes in intensity when changing $$\phi$$. We then make the second term zero by putting $$\phi$$ perpendicular to $$\theta$$. At this point we can simply subtract 45 degrees to put $$\phi$$ and $$\theta$$ at a 45 degree angle to make CPL.

### Wednesday 02/09/2026
- 9:00 Print front collimator holder
- 9:15 Make excel for fast axis alignment experiment
- 9:45 Setup experiment
- 10:15 Print opacity tool
- 10:30 Setup experiment
- 11:15 Print second front collimator holder
- 12:15 Visit: temporal resolution fluorescence spectrometer
- 13:00 Fast axis alignment measurements
- 14:30 3D print enclosure fit
- 17:00 Design new cuvette holder

#### Notes

##### Alignment experiment setup detector
I tried making the setup using a power and energy meter, but the noise due to temperature fluctuations seems to be too big. If I hold my hand in front of the detector or blow air, the noise is as big as 2-4x the signal. I have programmed a script (control_panel_alignment.py) to use the CCD to integrate the spectrum over a fixed range of wavelengths, which is less susceptible to noise.

Alignment to second linear polarizer: 5.1 degrees

Alignment to fresnel rhomb: 81.40 degrees

The excel crashed so I do not have the data from the first measurements anymore. I decided to automate the process in python for the data acquisition and simply look for the minimum.


### Thursday 03/09/2026
- 9:00 Print cuvette holder
- 9:30 Code broken pixel range indicator
- 10:00 Research CD formulas
- 10:30 Code absorbance and CD funtionalities
- 12:30 Debug code
- 13:30 Test measurement
- 15:00 Absorption spectra and make slides
- 16:00 Group meeting

#### Notes

##### To Do list until first prototype
In order of importance:

- Code Absorbance / CD spectrum functionalities
- Print new cuvette holder
- Design and print enclosure
- Reprint collimator holders
- Calculate/find handedness depending on angle
- Clean components

##### Absorption spectra
I tried to get some absorption spectra which look ok for the most part. I need to indicate the interval in which the light is intense enough to create a reliable signal, and also recheck the calibration as it seems to be off by around 20nm in the 700nm area. Luis provided me with minirods which show a peak at 750 on the commercial absorption spectrometer but 770nm in mine. However, the peak at 510nm lines up and the very first measurement I took did in fact show a peak at 750nm.
