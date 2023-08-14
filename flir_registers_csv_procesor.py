import cv2
import glob
import  os
import ctypes
from ctypes import *
import numpy as np
import cv2
from fireForestDetector import FireForestDetector
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

from fuzzySystemV2 import FuzzySystem

load_dotenv()

BUFFER_SIZE = 350000
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60
VISIBLE_IMAGE_HEIGTH = 1440
VISIBLE_IMAGE_WIDTH = 1080
CFLIRONE_CAPTURE_LIB = os.environ.get("CFLIRONE_CAPTURE_LIB")

cwd = os.getcwd()

cflironecapture = ctypes.CDLL(CFLIRONE_CAPTURE_LIB)

fireForestFuzzyDetector = FireForestDetector()

#altura = 8.6
#fligth_height = 40
thershold_temperature = 80
#flightSpeed = 30 #km/h
#overlap = 75
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60
#path_root = "./21-07-23"
path_root = "21-07-23"
path_csv = f"{path_root}/registers/fire_detection_2023_07_12_13_33_35_975324.csv" ## 1 metro cuadrado

#path_csv = f"{path_root}/registers/fire_detection_2023_07_21_12_31_11_264528.csv"
#path_csv = f"{path_root}/registers/fire_detection_2023_07_12_13_33_35_975324.csv" // mas de dos
path_images = f"{path_root}/images"

df = pd.read_csv(path_csv)

clibrary = ctypes.CDLL(CFLIRONE_CAPTURE_LIB)

gray16frame = (ctypes.c_uint16 * 4800)()
tframe_color = (ctypes.c_uint8 * (80*60* 3))()
temperatures = (ctypes.c_double * 4800)()

#pair_images = [
#    [f"{path_images}/flir_thermal_16gray_2023_06_09_08_04_01_997171.tiff",
#    f"{path_images}/flir_visible_image_2023_06_09_08_04_01_997171.jpg"]]
verdes = []
naranjas= []
rojos = []
probs =[]
for index ,row in df.iterrows():
    visible_image_path =  f'{path_root}/{row["visible_image"]}'
    thermal_image_path =  f'{path_root}/{row["thermal_image"]}'
    print("visible_image_path:", visible_image_path)
    print("thermal_image_path:", thermal_image_path)
    altura = row["alture"]

    path_tframe = (ctypes.c_char * 100)(*bytes(thermal_image_path, encoding="utf-8"))
    #path_vframe = (ctypes.c_char * 100)(*bytes(visible_image_path, encoding="utf-8"))

    clibrary.load_thermal_image_16bits_tiff.argtypes = [
    POINTER(ctypes.c_char),
    POINTER(ctypes.c_uint16)
    ]

    clibrary.load_thermal_image_16bits_tiff(path_tframe, gray16frame)

    minval_gray = ctypes.c_uint16(min(gray16frame))
    maxval_gray = ctypes.c_uint16(max(gray16frame))

    clibrary.read_tframe_color.argtypes = [ POINTER(ctypes.c_uint16), 
                                            POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint16),
                                            POINTER(ctypes.c_uint16)
                                            ]


    clibrary.read_tframe_color(gray16frame, tframe_color , byref(minval_gray), byref(maxval_gray))

    tframe_array = np.array(tframe_color, dtype= np.uint8)
    tframe_image = tframe_array.reshape((80,60,3))
    tframe_image = cv2.cvtColor(tframe_image, cv2.COLOR_RGB2BGR)

    #tframe_image = np.concatenate([tframe_image, np.zeros((20,60,3), dtype= np.uint8)], axis=0)
    

    clibrary.read_tframe_temperatures.argtypes = [
                                    POINTER(ctypes.c_uint16), 
                                    POINTER(ctypes.c_double),
                                    ]

    clibrary.read_tframe_temperatures(gray16frame, temperatures)


    vframe_image = cv2.imread(visible_image_path)
    
    temp_array = np.array(temperatures, dtype= np.float32)
    temp_array = temp_array.reshape(80, 60)

    mask_temp = temp_array > thershold_temperature
    mask_temp = mask_temp * 255
    mask_temp = mask_temp.astype(np.uint8)
    
    hot_regions_contours = fireForestFuzzyDetector.find_hot_regions(temp_array, thershold_temperature)
    max_areaM2 = fireForestFuzzyDetector.calculate_largest_area(hot_regions_contours, altura)
    max_temperature = fireForestFuzzyDetector.calcule_max_temperature(temp_array)
       
    fuzzySystem = FuzzySystem()
    
    rule_verde, rule_naranja , rule_rojo = fuzzySystem.fuzzy_inference(max_temperature, max_areaM2)
    print("rule_verde:", rule_verde)
    print("rule_naranja:", rule_naranja)
    print("rule_rojo:", rule_rojo)
    verdes.append(rule_verde)
    naranjas.append(rule_naranja)
    rojos.append(rule_rojo)
    output = fuzzySystem.defuzzification(rule_verde, rule_naranja , rule_rojo)
    probs.append(output.alert_prob)

df["rule_verde"] = verdes
df["rule_naranja"] = naranjas
df["rule_rojo"] = rojos
df["alert_prob"] = probs

os.makedirs("./new_precess", exist_ok= True)
df.to_csv(f'./new_precess/{path_csv.split("/")[-1]}')