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
thershold_temperature = 100
#flightSpeed = 30 #km/h
#overlap = 75
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60

path_csv = "./registers/fire_detection_2023_06_26_17_09_55_629175.csv"
path_images = "./images"

df = pd.read_csv(path_csv)

clibrary = ctypes.CDLL(CFLIRONE_CAPTURE_LIB)

gray16frame = (ctypes.c_uint16 * 4800)()
tframe_color = (ctypes.c_uint8 * (80*60* 3))()
temperatures = (ctypes.c_double * 4800)()

#pair_images = [
#    [f"{path_images}/flir_thermal_16gray_2023_06_09_08_04_01_997171.tiff",
#    f"{path_images}/flir_visible_image_2023_06_09_08_04_01_997171.jpg"]]

for index ,row in df.iterrows():
    visible_image_path =  row["visible_image"]
    thermal_image_path =  row["thermal_image"]
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

    tframe_image = np.concatenate([tframe_image, np.zeros((20,60,3), dtype= np.uint8)], axis=0)
    

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
    

    fireDetectionOuput = fireForestFuzzyDetector.detectFire(temp_array, altura, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH, thershold_temperature)
    alert_prob = fireDetectionOuput.fire_prob
    max_areaM2 = fireDetectionOuput.fireDetectionData.max_areaM2 
    max_temperature =  fireDetectionOuput.fireDetectionData.max_temperature
    print("alert_prob:", alert_prob)
    print("max_areaM2", max_areaM2)
    print("max_temperature", max_temperature)

    temp_str = str(round(max(temperatures), 2))
    area_str = str(round(max_areaM2, 3))
    tframe_image = cv2.putText(tframe_image, "Max:" + temp_str, (1,90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1, cv2.LINE_AA)
    #tframe_image = cv2.putText(tframe_image, "Area:" + area_str, (1,45), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1, cv2.LINE_AA)

    cv2.namedWindow("Mask Temperature", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Mask Temperature", 640, 480)
    cv2.imshow("Mask Temperature", mask_temp)

    cv2.namedWindow("Thermal Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Thermal Image", 640, 480)
    cv2.imshow("Thermal Image", tframe_image)
    
    ##vframe_image = cv2.convertScaleAbs(vframe_image, 1.3, 0)
    cv2.namedWindow("Visible Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Visible Image", 960, 720)
    cv2.imshow("Visible Image", vframe_image)
    max_temperature = temp_array.max()
    mask_array = temp_array > 100.0

    print("max_temperature:", max_temperature)
    mask_array = mask_array * 255.0
    mask_array = mask_array.astype(np.uint8)
    #ret,thresh = cv2.threshold(mask_array, 254, 255, cv2.THRESH_BINARY)

    #print(thresh)

    contours, hierarchy = cv2.findContours(mask_array, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    for i_cont in range(len(contours)):
        im_cont_i = np.zeros((80,60))
        areaPixels = cv2.contourArea(contours[i_cont])
        cv2.drawContours(im_cont_i, contours,  i_cont, (255, 255, 255), cv2.FILLED)
        
        im_hot_spot = im_cont_i != 0.0
        num_pixels = np.sum((im_hot_spot * 1.0))
        
        im_hot_spot = im_hot_spot * 255.0
        im_hot_spot = im_hot_spot.astype(np.uint8)
        
        cv2.namedWindow("Contours " + str(i_cont), cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Contours " + str(i_cont), 640, 480)
        cv2.imshow("Contours " + str(i_cont), im_hot_spot)

    cv2.waitKey(0)