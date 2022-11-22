import ctypes
from ctypes import *
import numpy as np
import cv2
from FireForestFuzzyDetector import FireForestFuzzyDetector
import socketio
from datetime import datetime
import time

#sio = socketio.Client()
#sio.connect('http://localhost:5055')


#sio.emit("startFireDetection", "Comienzar Detecction");
frameRate = 2
SH = 0.6136
SW = 0.620
hfov = 38
vfov = 50
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60
jpg_size = ctypes.c_uint32()
thermal_size = ctypes.c_uint32()
payload_size = ctypes.c_uint32()
tframe_data = (ctypes.c_uint8 * 350000)()
gray16frame = (ctypes.c_uint16 * 4800)()
temperatures = (ctypes.c_double * 4800)()
minval_gray = ctypes.c_uint16()
maxval_gray = ctypes.c_uint16()
tframe_color = (ctypes.c_uint8 * (80*60* 3))()
vframe_color = (ctypes.c_uint8 * (1440 * 1080 * 3))()
path = (ctypes.c_char * 100)(*b"./images")

tframe_image = np.zeros((80,60,3), dtype= np.uint8)

mask = np.zeros((80,60), dtype= np.uint8)

clibrary = ctypes.CDLL("./flironecapture.so")
 
device_handle = clibrary.open_device()

fireForestFuzzyDetector = FireForestFuzzyDetector()

altura = 10
thershold_temperature = 20
flightSpeed = 30 #km/h
overlap = 75


def calculateLongitudeVFov(altura):
    Vdv = 2 * altura * np.tan(0.5 * vfov * (np.pi / 180.0))

    Tdv = Vdv * SH
    return Tdv

def calculateFps(altura):
    dv =  calculateLongitudeVFov(altura)
    return  (flightSpeed  * 18/5) / ((1 - overlap) * dv)
    
frameRate = calculateFps(altura)

while True:
    clibrary.read_tframe(device_handle, tframe_data , byref(jpg_size), byref(thermal_size), byref(payload_size))

    clibrary.read_gray16_scale.argtypes = [ POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint16), 
                                            POINTER(ctypes.c_uint32),
                                            POINTER(ctypes.c_uint16),
                                            POINTER(ctypes.c_uint16)
                                            ]

    clibrary.read_gray16_scale(tframe_data, gray16frame, byref(jpg_size), byref(minval_gray), byref(maxval_gray))



    clibrary.read_tframe_color.argtypes = [ POINTER(ctypes.c_uint16), 
                                            POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint16),
                                            POINTER(ctypes.c_uint16)
                                            ]


    clibrary.read_tframe_color(gray16frame, tframe_color , byref(minval_gray), byref(maxval_gray))

    clibrary.read_tframe_temperatures.argtypes = [
                                        POINTER(ctypes.c_uint16), 
                                        POINTER(ctypes.c_double),
                                        ]

    clibrary.read_tframe_temperatures(gray16frame, temperatures)
    
    clibrary.read_frame_color.argtypes = [
                                            POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint32),
                                            POINTER(ctypes.c_uint32),
                                            ctypes.c_uint32,
                                            ctypes.c_uint32
                                        ]

                    

    tframe_array = np.array(tframe_color, dtype= np.uint8)
    tframe_image = tframe_array.reshape((80,60,3))
    
    temp_array = np.array(temperatures, dtype= np.float32)
    temp_array = temp_array.reshape(80, 60)
    
    ## Fire detection
    prevTime = 0
    time_elapsed = time.time() - prevTime
    #t = time.time()
    #t_ms = int(t * 1000)
    
    if (time_elapsed > (1 / frameRate)):

        clibrary.save_flirone_images.argtypes = [
            POINTER(ctypes.c_char),
            POINTER(ctypes.c_uint16),
            ctypes.c_uint32,
            ctypes.c_uint32,
            POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]


        if(clibrary.read_frame_color(tframe_data, vframe_color, thermal_size, jpg_size, 1440,1080)):
            Vframe_array = np.array(vframe_color, dtype= np.uint8)
            Vframe_image = Vframe_array.reshape((1440,1080,3))
                    
            cv2.namedWindow("VisibleImage", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("VisibleImage", 640, 480)
            cv2.imshow("VisibleImage", Vframe_image)
                    
            clibrary.save_flirone_images(path, gray16frame, 60, 80, vframe_color, 1080,1440)
        
        alert_prob, max_areaM2, max_temperature = fireForestFuzzyDetector.detectFire(temp_array, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH, thershold_temperature)
        
        print("alert_prob:", alert_prob)

        if alert_prob > 0.2:
            now = datetime.now() # current date and time
            date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

            data = {
                "maxTemperature": str(max_temperature),
                "areaFire": str(max_areaM2),
                "latitud": "0",
                "longitud": "0",
                "distance": str(altura),
                "time": date_time
            }

            #sio.emit("fireDetected", data)
        
    cv2.namedWindow("Thermal Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Thermal Image", 640, 480)
    cv2.imshow("Thermal Image", tframe_image)

    if cv2.waitKey(1) == ord('q'):
        break
    
cv2.destroyAllWindows()

#sio.emit("stopFireDetection", "Detener Detecction")