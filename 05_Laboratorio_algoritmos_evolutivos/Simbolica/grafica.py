import numpy as np
import matplotlib.pyplot as plt

# Generar 1000 valores entre 0.0 y 1.0
x = np.linspace(-10.0, 10.0, 1000)
#y = 6.67 + 11 * cos(7.23*x**3)
y = 6.67 + 11 * np.cos(7.23*x**3)
#de 0 a 1
# Función matemática
#y = (np.sin((5 * np.pi) * x))**6 * np.exp(-2 * np.log(2) * ((x - 0.1) / 0.8))



# Graficar
plt.plot(x, y)
plt.xlabel("x")
plt.ylabel("f(x)")
plt.title("Gráfica de la función")
plt.grid(True)
plt.show()