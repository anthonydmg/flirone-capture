import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt

HFOV_half = math.radians(50 / 2)
VFOV_half = math.radians(38 / 2)
ALTURA = 15 # metros
delta_HFOV = math.radians(1)
delta_VFOV = math.radians(1)

HORIZONTAL_RESOLUTION = 80
VERTICAL_RESOLUTION = 60

delta_ALTURA = 1 + 1 + 1.0

def pixeles_to_m2(pixels, altura):
    GSD_H = (2 * math.tan(HFOV_half) * altura) / HORIZONTAL_RESOLUTION
    GSD_V = (2 * math.tan(VFOV_half) * altura) / VERTICAL_RESOLUTION
    area = pixels * GSD_H * GSD_V
    return area 

def m2_to_pixels(meters, altura):
    GSD_H = (2 * math.tan(HFOV_half) * altura) / HORIZONTAL_RESOLUTION
    GSD_V = (2 * math.tan(VFOV_half) * altura) / VERTICAL_RESOLUTION
    pixels = meters / (GSD_H * GSD_V)
    return pixels

def calcule_delta_area(altura, pixels):
    GSD_H = (2 * math.tan(HFOV_half) * altura) / HORIZONTAL_RESOLUTION
    GSD_V = (2 * math.tan(VFOV_half) * altura) / VERTICAL_RESOLUTION

    delta_tan_HFOV = ((1/ math.cos(HFOV_half)) ** 2) * 0.5 * delta_HFOV


    delta_tan_VFOV = ((1/ math.cos(VFOV_half)) ** 2) * 0.5 * delta_VFOV

    print("delta_tan_HFOV:", delta_tan_HFOV)
    print("delta_tan_VFOV:", delta_tan_VFOV)
    delta_GSD_H = (2 / HORIZONTAL_RESOLUTION) * ( ALTURA * abs(delta_tan_HFOV) + delta_ALTURA * abs(math.tan(HFOV_half))) 
    delta_GSD_V = (2 / VERTICAL_RESOLUTION) * ( ALTURA * abs(delta_tan_VFOV) + delta_ALTURA * abs(math.tan(VFOV_half))) 

    print("delta_GSD_H:", delta_GSD_H)
    print("delta_GSD_V:", delta_GSD_V)

    delta_area = GSD_H * delta_GSD_V + delta_GSD_H * GSD_V * pixels

    return delta_area


pix_1m = m2_to_pixels(meters= 1, altura= 15)

delta_area_h15m_1m = calcule_delta_area(altura= 15, pixels = pix_1m)

plt.vlines(1, 0, delta_area_h15m_1m, color='red', linestyle='--')

plt.hlines(delta_area_h15m_1m, 0, 1, color='red', linestyle='--')


pix_2m = m2_to_pixels(meters= 2, altura= 15)

delta_area_h15m_2m = calcule_delta_area(altura= 15, pixels = pix_2m)

plt.vlines(2, 0, delta_area_h15m_2m, color='red', linestyle='--')

plt.hlines(delta_area_h15m_2m, 0, 2, color='red', linestyle='--')

pix_5m = m2_to_pixels(meters= 5, altura= 15)

delta_area_h15m_2m = calcule_delta_area(altura= 15, pixels = pix_5m)

plt.vlines(5, 0, delta_area_h15m_2m, color='red', linestyle='--')

plt.hlines(delta_area_h15m_2m, 0, 5, color='red', linestyle='--')


pix_10m = m2_to_pixels(meters= 10, altura= 15)

delta_area_h15m_2m = calcule_delta_area(altura= 15, pixels = pix_10m)

plt.vlines(10, 0, delta_area_h15m_2m, color='red', linestyle='--')

plt.hlines(delta_area_h15m_2m, 0, 10, color='red', linestyle='--')


pixels = np.arange(1, 500, 1)
area_15m = pixeles_to_m2(pixels=pixels, altura= 15)
delta_area_h15m = calcule_delta_area(altura= 15, pixels = pixels)
plt.plot(area_15m, delta_area_h15m, alpha=0.8, label = "15 m Altura")

pix_1m = m2_to_pixels(meters= 1, altura= 20)
delta_area_h20m_1m = calcule_delta_area(altura= 20, pixels = pix_1m)

plt.hlines(delta_area_h20m_1m, 0, 1, color='red', linestyle='--')

pix_2m = m2_to_pixels(meters= 2, altura= 20)
delta_area_h20m_1m = calcule_delta_area(altura= 20, pixels = pix_2m)

plt.hlines(delta_area_h20m_1m, 0, 2, color='red', linestyle='--')

pix_5m = m2_to_pixels(meters= 5, altura= 20)
delta_area_h20m_1m = calcule_delta_area(altura= 20, pixels = pix_5m)

plt.hlines(delta_area_h20m_1m, 0, 5, color='red', linestyle='--')

pix_10m = m2_to_pixels(meters= 10, altura= 20)
delta_area_h20m_1m = calcule_delta_area(altura= 20, pixels = pix_10m)

plt.hlines(delta_area_h20m_1m, 0, 10, color='red', linestyle='--')

pixels = np.arange(1, 280, 1)

area_20m = pixeles_to_m2(pixels=pixels, altura= 20)
delta_area_20m = calcule_delta_area(altura= 20, pixels = pixels)
plt.plot(area_20m, delta_area_20m, alpha=0.8, label = "20 m Altura")

#plt.scatter(area_20m, delta_area_20m, label = "20 m Altura", alpha=0.5)

plt.ylabel("Δ Area M²")

plt.xlabel("Area M²")
plt.ylim(ymin=0)
plt.xlim(xmin=0)
plt.yticks(np.arange(0, 3.5, step=0.25))
plt.xticks(np.arange(0, 15, step=1))
plt.legend()
plt.show()