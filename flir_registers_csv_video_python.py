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
thershold_temperature = 80
#flightSpeed = 30 #km/h
#overlap = 75
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60

path_root = "./25-07-23"
path_csv = f"{path_root}/registers/fire_detection_2023_07_25_16_56_46_820618.csv"
#path_csv = f"{path_root}/registers/fire_detection_2023_07_12_13_33_35_975324.csv" // mas de dos
path_images = f"{path_root}/images"

df = pd.read_csv(path_csv)

#pair_images = [
#    [f"{path_images}/flir_thermal_16gray_2023_06_09_08_04_01_997171.tiff",
#    f"{path_images}/flir_visible_image_2023_06_09_08_04_01_997171.jpg"]]

for index ,row in df.iterrows():
    visible_image_path =  f'{path_root}/{row["visible_image"]}'
    thermal_image_path =  f'{path_root}/{row["thermal_image"]}'
    
    gray16_image = cv2.imread(thermal_image_path, cv2.IMREAD_ANYDEPTH)
    print("Max gray16: ", gray16_image.max())
    print("Min gray16: ", gray16_image.min())
    gray16_image[ gray16_image > np.percentile(gray16_image, 90)] = gray16_image.mean()
    im_shape = gray16_image.shape
    gray8_image = np.zeros(im_shape, dtype = np.uint8)
    gray8_image = cv2.normalize(gray16_image, gray8_image,0, 255, cv2.NORM_MINMAX)
    gray8_image = np.uint8(gray8_image)
    inferno_palette_img = cv2.applyColorMap(gray8_image, cv2.COLORMAP_JET)

    altura = row["alture"]

    #path_vframe = (ctypes.c_char * 100)(*bytes(visible_image_path, encoding="utf-8"))
    
    vframe_image = cv2.imread(visible_image_path)
    
    #temp_array = np.array(temperatures, dtype= np.float32)
    #temp_array = temp_array.reshape(80, 60)

    #mask_temp = temp_array > thershold_temperature
    #mask_temp = mask_temp * 255
    #mask_temp = mask_temp.astype(np.uint8)
    

    #fireDetectionOuput = fireForestFuzzyDetector.detectFire(temp_array, altura, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH, thershold_temperature)
    #alert_prob = fireDetectionOuput.fire_prob
    #max_areaM2 = fireDetectionOuput.fireDetectionData.max_areaM2 
    #max_temperature =  fireDetectionOuput.fireDetectionData.max_temperature
    #print("alert_prob:", alert_prob)
    #print("max_areaM2", max_areaM2)
    #print("max_temperature", max_temperature)
    #print("altura:", altura)

    #temp_str = str(round(max(temperatures), 2))
    #area_str = str(round(max_areaM2, 3))
    #tframe_image = cv2.putText(tframe_image, "Max:" + temp_str, (1,90), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1, cv2.LINE_AA)
    #tframe_image = cv2.putText(tframe_image, "Area:" + area_str, (1,45), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,0), 1, cv2.LINE_AA)
    tframe_image_resize = cv2.resize(inferno_palette_img,(1080,1440), cv2.INTER_AREA)
    
    
    cv2.namedWindow("Thermal Image", cv2.WINDOW_NORMAL)

    cv2.resizeWindow("Thermal Image", 640, 480)
    cv2.imshow("Thermal Image", inferno_palette_img)
    
    ##vframe_image = cv2.convertScaleAbs(vframe_image, 1.3, 0)
    cv2.namedWindow("Visible Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Visible Image", 960, 720)
    #cv2.imshow("Thermal Image Resize", tframe_image_resize)
    cv2.imshow("Visible Image", vframe_image)
    gray = cv2.cvtColor(vframe_image, cv2.COLOR_BGR2GRAY)
    # blur the image
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    t_lower = 50  # Lower Threshold
    t_upper = 200  # Upper threshold
    vframe_edges = cv2.Canny(blurred, t_lower, t_upper)
    #cv2.imshow("Visible Image Edges", vframe_edges)
    tframe_image_add_edges = cv2.addWeighted(tframe_image_resize, 0.7, cv2.cvtColor(vframe_edges, cv2.COLOR_GRAY2BGR), 0.3,0)
    #cv2.namedWindow("Thermal Image Edges", cv2.WINDOW_NORMAL)
    #cv2.resizeWindow("Thermal Image Edges",  960, 720)
    #cv2.imshow("Thermal Image Edges", tframe_image_add_edges)
   
    cv2.waitKey(0)