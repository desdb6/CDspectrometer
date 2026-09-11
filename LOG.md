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

### Friday 03/09/2026
- 9:00 Design and print front collimator holder
- 9:45 Fix polarization convention
- 10:15 Design back collimator holder
- 10:45 CD measurement
- 11:00 Print back collimator holder
- 11:30 Beam alignment experiments (many)
- 14:30 Fabry Perot test

#### Notes
##### To Do list
- Print collimator holders to fix alignment
- Recalibrate 700nm wavelength range
- Program intensity cutoff indicator
- Measure more CD signals and look at oscillations

##### CD artefacts
Even without a sample, we get a significant CD signal. This could be cause by a number of things.

- The beam tilt: We can observe that the front collimator holder is slightly tilted which causes the beam to not travel parallel to the horizontal axis, but upwards. This could be due to removing the print from the printbed too fats which can cause warping. Later prints that were cooled down completely seemed to be aligned well. This tilt can mess with the polarization state as the incident angles for the total internal reflection will be different. Trying to align the beam gave results that are a little better in the 400-750nm range but worse around 1000nm. However trying to make the alignment worse by triyng to tilt the beam down a lot made it better overall.
- Fast axis alignment
- Dust on the linear polarizer: As the polariser turns, the beam will fall on a different spot on the polarizer which can cause differences in absorption
- There is a oscillating signal which looks to be linear with the frequency (also present without fresnel rhomb). My theory is that the beam is diffracting at the polarizer in a different way if the polarizer is horizontal and vertical, but I still need to test this.
- Fabry perot etalon somewhere

##### To Do for next week
- Clean the polarizer
- Figure out the CD artefacts
- Make program more user friendly: error handling, user guide etc
- Make icon for program
- Discuss journal?
- Design adjustable collimator holders
- Design smaller cuvette holder
- Make parts for UV-Vis absorption modular setup

### Monday 07/09/2026
- 9:00 Print front collimator holder
- 9:30 Test misalignments and figure out CD artefacts
- 10:30 Design and print fiber holder
- 11:00 Make code more user friendly
- 11:30 Rebuild setup
- 12:00 Turning collimator experiment
- 12:30 Print collimator holder
- 13:00 Make code more user friendly and make executable
- 15:00 Print fiber holder
- 15:30 Clean components
- 17:00 Realign components
- 17:30 Write user manual
- 18:00 More CD measurements

#### Notes
##### CD artefacts
I spent the morning trying and tweaking different components of the setup. The spectra I took can be found in the outputs folder for this date. Translation does not seem to make a great difference, but the rotation of the collimators seems to show a cosine-like effect on the overall intensity. This is true for **both** collimators, the front and the back. Rotating one of them also flips the CD spectra, but it is not as linear as I would have hoped. I decided to clean all the components to see if this is an improvement but for this the components also need to be realigned. In the end this did not seem to make a huge difference. Frustrating day :(

### Tuesday 08/09/2026
- 9:00 Design and print absorption spectroscopy cuvette holder
- 9:30 Rebuild setup
- 9:45 Try to recreate CD artefacts
- 11:00 Call Carlos
- 11:45 Program CD baseline correction
- 12:30 Recalibrate CCD
- 13:30 Absorption measurements
- 14:45 Print fiber holder
- 15:00 Program CD baseline correction, fix bugs, improve usability
- 15:30 Recalibration using Holmium oxide glass
- 16:00 Absorption measurements
- 16:30 Improve code usability
- 17:00 Helicoid CD measurements
- 17:30 Prepare overnight print

#### Notes
##### CD artefacts
The spectra I took can be found in the outputs folder for this date. My first idea today was to se a different polarizer and move it by hand, but this resulted in the same artefacts with a double peak, confirming the polarizer is not the problem. 

##### Call Carlos
Carlos said that it is known that the fiber position has a very big influence on the spectrum, and that it is very difficult to stabilize this. He suggests taking baseline measurements and correcting in software. Furthermore, if might be better to work in absorbance units. He also suggested a way to calibrate the CCD using a rare earth metal glass for small absorbance peaks. Finally he said we could be open to use free space light instead of fibers in the future.

### Wednesday 09/09/2026
- 9:00 Print cuvette holder
- 9:30 Figure sign flip out
- 11:00 Print cuvette holder
- 12:00 Helicoid CD measurements
- 13:00 Compare to Jasco CD
- 15:00 Compare data to Huu-Quang
- 15:30 Reduce noise in setup
- 17:30 Prepare overnight print

#### Notes

### Thursday 10/09/2026
- 9:00 (re-)Build absorbance and CD setups
- 9:30 Print collimator holder
- 10:00 Make plot buttons better
- 11:00 Cysteine CD measurements
- 11:30 Helicoid dilution experiment
- 12:30 Make group meeting slides
- 14:00 Absorption dilution experiment
- 16:00 Group meeting
- 17:00 Fix absorption baseline issue

#### Notes
##### Helicoid dilution experiment
To test the limit of what can be measured I will perform an experiment where I dilute the helicoid samples and see if I can still measure a CD signal. I will do dilutions of 1x, 5x, 25x and 125x. I do this by preparing dilutions by pipetting 30mul of the undiluted helicoids in a cuvette with 120mul of 1mM CTAB. Then I repeat this process 2 more times to make the other dilutions, making sure the sample is homogenous every time. I will take a baseline measurement before each CD measurement.

### Friday 11/09/2026
- 9:00 Final code changes

#### Notes
##### Pyinstaller command
"C:\Users\lguser\AppData\Local\Programs\Python\Python311-32\python.exe" -m PyInstaller --onefile --windowed --icon=cd.ico --add-data "SP_SDK;SP_SDK" main.py
