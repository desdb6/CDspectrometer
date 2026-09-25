import numpy as np
import matplotlib.pyplot as plt

wavelength_values = [418.5, 453.4, 459.9, 536.4, 637.5]
pixel_values = [989, 1119, 1143, 1423, 1787]

coeffs = np.polyfit(wavelength_values, pixel_values, 3)
poly = np.poly1d(coeffs)

x_fit = np.linspace(250, 1250, 300)
y_fit = poly(x_fit)

plt.figure(figsize=(6, 4.5))
plt.scatter(wavelength_values, pixel_values, color='crimson', label='Data', zorder=3)
plt.plot(x_fit, y_fit, color='steelblue', label='3rd degree fit', zorder=2)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Pixel')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()