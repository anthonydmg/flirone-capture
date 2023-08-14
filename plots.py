import matplotlib.pyplot as plt
import numpy as np

# Datos para el gráfico de línea
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Posición en el eje x donde quieres trazar la línea vertical
x_intersection = 3

# Crear el gráfico de línea
plt.plot(x, y, label='Función seno')

# Trazar la línea vertical hasta el gráfico de la función
plt.vlines(x_intersection, -1, np.sin(x_intersection), color='red', linestyle='--', label='Intersección')

# Personalizar el gráfico
plt.xlabel('Eje X')
plt.ylabel('Eje Y')
plt.title('Gráfico de Línea con Línea Vertical de Intersección')
plt.legend()
plt.grid(True)

# Mostrar el gráfico
plt.show()