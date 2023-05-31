import argparse
import math
import time 
from bmp280 import BMP280
import json
import os
from utils import create_csv, register_in_csv

try:
   from smbus2 import SMBus
except ImportError:
   from smbus import SMBus

P0 = 11000 # presion en el puntho inicial

C = 8453.669 

PRESION_OVER_SEA_LEVEL = 1013.25

class Altimeter:
  # def __init__(self):
   def connect(self):
      try:
         bus = SMBus(1)
         self.bmp280 = BMP280(i2c_dev = bus)

         if not os.path.isfile("altimeter_params.json"):
            self.inicialize_p0()
         else:
            with open("altimeter_params.json", "r") as f:
               params = json.load(f)
               print(params)
               self.P0 = params["P0"]

         return True

      except Exception as err:
         print(f"Error {err=}, {type(err)=}")
         return False
   
   def inicialize_p0(self):
      print("Inicializando Presion de region base (P0)...")
      self.P0 = self.read_pressure()
      num_reads = 20
      delay = 1 # retraso en segundos
      cum_P = 0
      for _ in range(num_reads):
         P = self.read_pressure()
         cum_P += P
         time.sleep(1.0)
      
      self.P0 = cum_P/ num_reads
      print("Guardando P0 en alimeter_params.json")
      with open("altimeter_params.json", "w") as f:
         json.dump({"P0": self.P0},f)

   def read_pressure(self):
      return self.bmp280.get_pressure()

   def calculate_absolute_alture(self, P0, P):
      return 8453.669 * math.log(P0/P)

   def read_absolute_alture(self):
      P = self.read_pressure()
      print("Presion P:", P)
      return self.calculate_absolute_alture(self.P0, P)
   
   def read_alture_over_sea_level(self):
      P = self.read_pressure()
      return self.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL, P)

def inicializate_altimeter():
   altimeter = Altimeter()
   altimeter.inicialize_p0()

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description = "altimeter BMP280",
				    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
   parser.add_argument("-i", "--init", default = False)
   
   args = parser.parse_args()
   config = vars(args)
   print(config)
   
   init = True if config["init"] == "True" else False
   altimeter = Altimeter()
   altimeter.connect()
   if init == True:
      altimeter.inicialize_p0()
      P0 = altimeter.P0
      P =  altimeter.read_pressure()
      print("Presion en superficie base: ", P0)
      h_sea_level = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL, P)
      print("Altura sobre el nivel del mar: ", h_sea_level)
   else:
      file_name = create_csv(name_base = "altimeter_", req_fields = ["presion", "alture_over_sea_level", "abs_alture"])
      while True:
         P = altimeter.read_pressure()
         P0 = altimeter.P0
         h_sea_level = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL,P)
         h = altimeter.calculate_absolute_alture(P0,P)
         data = {"presion":P ,"presion_over_floor": P0, "alture_over_sea_level": h_sea_level, "abs_alture": h}
         register_in_csv(file_name, data, req_fields = ["presion","presion_over_floor", "alture_over_sea_level", "abs_alture"])
         time.sleep(0.8)
      #P = altimeter.read_pressure()
      #P0 = altimeter.P0
      #h_sea_level = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL,P)
      #h = altimeter.calculate_absolute_alture(P0,P)
      #print("Altura sobre el nivel del mar:", h_sea_level)
      #print("Altitud:", h)
      #print("Presion:", P)
