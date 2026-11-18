
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Generar 1000 valores entre -10.0 y 10.0
x = np.linspace(-10, 10, 1000)
#y = 6.67 + 11 * cos(7.23*x**3)
#y = 6.67 + 11 * np.cos(7.23*x**3)
y = 2*(x**2)
#de 0 a 1
# Función matemática
#y = (np.sin((5 * np.pi) * x))**6 * np.exp(-2 * np.log(2) * ((x - 0.1) / 0.8))



# Guardar exactamente los puntos que se van a graficar.
ruta_csv = Path(__file__).with_suffix('.csv')
np.savetxt(ruta_csv, np.column_stack((x, y)), delimiter=',',
           header='x,y', comments='')
print(f'CSV generado: {ruta_csv} ({len(x)} puntos)')

# Graficar
plt.plot(x, y)
plt.xlabel("x")
plt.ylabel("f(x)")
plt.title("Gráfica de la función")
plt.grid(True)
plt.show()
