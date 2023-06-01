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
               self.altitude_over_sea_level_lib_adafruit = params.get("altitude_over_sea_level_lib_adafruit", 0)
               self.altitude_over_sea_level_lib_bmp280 = params.get("altitude_over_sea_level_lib_bmp280", 0)
               

         return True

      except Exception as err:
         print(f"Error {err=}, {type(err)=}")
         return False
   
   def inicialize_p0(self):
      print("Inicializando Presion de region base (P0)...")
      self.P0 = self.read_pressure()
      num_reads = 10
      delay = 1 # retraso en segundos
      cum_P = 0
      cum_altitude_over_sea_level_lib_bmp280 = 0
      cum_altitude_over_sea_level_lib_adafruit = 0
      for _ in range(num_reads):
         P = self.read_pressure()
         cum_P += P
         cum_altitude_over_sea_level_lib_bmp280 += self.read_altitude_lib_bmp280()
         cum_altitude_over_sea_level_lib_adafruit += self.read_altitude_lib_bmp280()
         time.sleep(1.0)
      
      self.P0 = cum_P/ num_reads
      self.altitude_over_sea_level_lib_bmp280 = cum_altitude_over_sea_level_lib_bmp280 / num_reads
      self.altitude_over_sea_level_lib_adafruit = cum_altitude_over_sea_level_lib_adafruit / num_reads
      
      print("Guardando P0 en alimeter_params.json")
      with open("altimeter_params.json", "w") as f:
         json.dump({ "P0": self.P0, 
                     "altitude_over_sea_level_lib_bmp280": self.altitude_over_sea_level_lib_bmp280,
                     "altitude_over_sea_level_lib_adafruit": self.altitude_over_sea_level_lib_adafruit
                     },f)

   def read_altitude_lib_bmp280(self):
      return self.bmp280.get_altitude()

   def read_altitude_lib_adafruit(self, P):
      return 44330 * (1.0 - math.pow(P / PRESION_OVER_SEA_LEVEL, 0.1903))

   def read_pressure(self):
      return self.bmp280.get_pressure()
   def read_temperature(self):
      return self.get_temperature()

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
      print("Promedio de altitud sobre el nivel del mar con la libreria: ", altimeter.altitude_over_sea_level)
      h_sea_level = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL, P)
      print("Calculo propio de altura sobre el nivel del mar: ", h_sea_level)
   else:
      req_fields = [ "presion",
                     "presion_over_floor", 
                     "altitude_over_sea_level_lib_bmp280", 
                     "altitud_over_sea_level_lib_adafruit",
                     "altitud_over_sea_level_calculada", 
                     "calculate_abs_alture", 
                     "calculate_abs_alture_diff_lib_bmp280",
                     "calculate_abs_alture_diff_lib_adafruit"]

      file_name = create_csv(name_base = "altimeter_", req_fields = req_fields)
      while True:
         P = altimeter.read_pressure()
         P0 = altimeter.P0
         h_sea_level_calculada = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL,P)
         h_sea_level_lib_bmp280 = altimeter.read_altitude_lib_bmp280()
         h_sea_level_lib_adafruit = altimeter.read_altitude_lib_adafruit(P)
         h_abs_calculate = altimeter.calculate_absolute_alture(P0,P)
         h_abs_calculate_diff_lib_bm280 = h_sea_level_lib_bmp280 - altimeter.altitude_over_sea_level_lib_bmp280
         h_abs_calculate_diff_lib_adafruit = h_sea_level_lib_adafruit - altimeter.altitude_over_sea_level_lib_adafruit
         
         temperature = altimeter.read_temperature()
         
         data = {
            "presion":P ,
            "presion_over_floor": P0, 
            "altitude_over_sea_level_lib_bmp280": h_sea_level_lib_bmp280,
            "altitud_over_sea_level_lib_adafruit": h_sea_level_lib_adafruit,
            "altitud_over_sea_level_calculada": h_sea_level_calculada,
            "calculate_abs_alture": h_abs_calculate, 
            "calculate_abs_alture_diff_lib_bmp280": h_abs_calculate_diff_lib_bm280,
            "calculate_abs_alture_diff_lib_adafruit": h_abs_calculate_diff_lib_adafruit
         }
         
         print("\nData:", data)
         register_in_csv(file_name, data, req_fields = req_fields)
         time.sleep(0.8)
      #P = altimeter.read_pressure()
      #P0 = altimeter.P0
      #h_sea_level = altimeter.calculate_absolute_alture(PRESION_OVER_SEA_LEVEL,P)
      #h = altimeter.calculate_absolute_alture(P0,P)
      #print("Altura sobre el nivel del mar:", h_sea_level)
      #print("Altitud:", h)
      #print("Presion:", P)
