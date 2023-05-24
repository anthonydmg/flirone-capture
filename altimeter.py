import math
import time 
from bmp280 import BMP280
import json
import os

try:
   from smbus2 import SMBus
except ImportError:
  from smbus import SMBus

#print("Temperatura y presion:\n")

P0 = 11000 # presion en el puntho inicial

C = 8453.669 

PRESION_OVER_SEA_LEVEL = 1013.25

class Altimeter:
   def __init__(self):
      bus = SMBus(1)
      self.bmp280 = BMP280(i2c_dev = bus)
      if not os.path.isfile("altimeter_params.json"):
         self.inicialize_p0()
      else:
         with open("altimeter_params.json", "r") as f:
            params = json.load(f)
            print(params)
            self.P0 = params["P0"]
            
   def inicialize_p0(self):
      self.P0 = self.read_pressure()
      with open("altimeter_params.json", "w") as f:
         json.dump({"P0": self.P0},f)

   def read_pressure(self):
      return self.bmp280.get_pressure()

   def read_abolute_alture(self):
      P = self.read_pressure()
      return 8453.669 * math.log(self.P0/P)
   def read_alture_over_sea_level(self):
      P = self.read_pressure()
      return 8453.669 * math.log(PRESION_OVER_SEA_LEVEL/P)


altimeter = Altimeter()

h =  altimeter.read_abolute_alture()
P = altimeter.read_pressure()
h_sea_level = altimeter.read_alture_over_sea_level()

print("Altura sobre el nivel del mar:", h_sea_level)
print("Altitud:", h)
print("Presion:", P)
