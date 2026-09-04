import matplotlib.pyplot as plt
import numpy as np

data_ref = np.loadtxt(r"Outputs\CD_ref", skiprows=1)
data_sig = np.loadtxt(r"Outputs\CD1", skiprows=1)

plt.plot(data_ref[:, 1], data_sig[:, 2]-data_ref[:, 2])
plt.grid()
plt.show()