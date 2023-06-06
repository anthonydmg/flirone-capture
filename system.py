import ctypes
from ctypes import *
import numpy as np
import cv2
from fuzzySystem import FuzzySystem
import socketio
from datetime import datetime
import time
from flirone_capture import FlirOneCapture
import gc

from module_radar import ModuleDistanceDetector
from gps_reciver import GPS_RECEIVER
import threading
from fireForestDetector import FireForestDetector, FireDetecionData, FireDetectionOuput
from utils import StreamingMovingAverage
from altimeter import Altimeter, PRESION_OVER_SEA_LEVEL
from utils import create_csv, register_in_csv

FRAME_RATE = 1

THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60

INIT_FLIGHT_HEIGHT = 10
INIT_FLIGHT_SPEED = 30
stop_read_radar = False
stop_read_location = False
stop_read_bmp280 = False
SH = 0.6136
SW = 0.620
hfov = 38
vfov = 50
CURRENT_ALTURE = INIT_FLIGHT_HEIGHT
CURRENT_LOCATION = {"latitude": "", "longitude": ""}

CURRENT_ALTIMETER_DATA = { 
         "presion": 0,  
         "alture": 0, 
         "alture_over_sea_level": 0,
         "environment_temperature": 0,
         "alture_lib_adafruit": 0,
         "alture_lib_bm280": 0 
        }


def read_location(stop_read, gps_reciever):
    while True:
        #print("Thread runing Location")
        location = gps_reciever.get_current_location()
        print("Read location: \n", location)
        if location["latitude"]!= "" and location["longitude"]!= "":
            CURRENT_LOCATION["latitude"] = location["latitude"]
            CURRENT_LOCATION["longitude"] = location["longitude"]
        time.sleep(0.2)
        if stop_read():
            break

def read_alture(stop_read, altimeter):
    #global CURRENT_ALTURE
    #streaming_moving_average = StreamingMovingAverage(5)
    while True:
        P = altimeter.read_pressure()
        temperature = altimeter.read_temperature()
        altitud_lib_bmp280 = altimeter.read_altitude_lib_bmp280(manual_temperature = temperature)
        altitud_lib_adafruit = altimeter.read_altitude_lib_adafruit(P)
        
        abs_h_lib_adafruit = altitud_lib_adafruit - altimeter.altitude_over_sea_level_lib_adafruit
        abs_h_lib_bm280 = altitud_lib_bmp280 - altimeter.altitude_over_sea_level_lib_bmp280
        
        CURRENT_ALTIMETER_DATA["presion"] = P
        CURRENT_ALTIMETER_DATA["environment_temperature"] = temperature
        CURRENT_ALTIMETER_DATA["alture"] = abs_h_lib_adafruit
        CURRENT_ALTIMETER_DATA["altitud_over_sea_level"] =  altimeter.altitude_over_sea_level_lib_adafruit
        CURRENT_ALTIMETER_DATA["altitud_over_sea_level_lib_bmp280"] = altimeter.altitude_over_sea_level_lib_bmp280
        CURRENT_ALTIMETER_DATA["altitude_over_sea_level_lib_adafruit"] = altimeter.altitude_over_sea_level_lib_adafruit
        CURRENT_ALTIMETER_DATA["alture_lib_adafruit"] = abs_h_lib_adafruit
        CURRENT_ALTIMETER_DATA["alture_lib_bm280"] = abs_h_lib_bm280

        time.sleep(0.5)
        if stop_read():
            break

def read_distance(stop_read):
    while True:
        print("Thread runing")
        distance = distanceDetector.read()
        if distance != 0:
            data["distance_xm132"] = distance
            #frameRate = calculateFps(fligth_height)
        time.sleep(0.4)
        if stop_read():
            distanceDetector.close()
            break

class System:
    def __init__(self, frame_rate = FRAME_RATE, fligth_height = INIT_FLIGHT_HEIGHT , fligh_speed = INIT_FLIGHT_SPEED, show_frames = False, overlap = 0.75):
        self.flirone_capture = FlirOneCapture()
        self.sio = socketio.Client()
        self.distanceDetector = ModuleDistanceDetector()
        self.fireForestDetector = FireForestDetector()
        self.frame_rate = frame_rate
        self.fligth_height = fligth_height
        self.fligh_speed = fligh_speed
        self.show_frames = show_frames
        self.overlap = overlap
        self.gps_reciever = GPS_RECEIVER()
        self.altimeter = Altimeter()

    def run(self):
        ## Connect Flir one
        opened = self.flirone_capture.open_device()

        if opened:
         print("Dispositivo conectado existosamente")
        else:
            print("Ocurrio un error al memento de abrir dispositivo")
            exit(0)
        ## Conenct Websockets to Interface
        self.sio.connect('http://localhost:5055', wait_timeout = 10)
        self.sio.emit("startFireDetection", "Comienzar Detecction")

        ## Connect Module Radar
        success_xm132 = self.distanceDetector.connect()

        if success_xm132:
            print("XM132 conectado exitosamente")
            self.start_read_distance()
        else:
            print("XM132 no se puedo conectar")

        succes_altimeter = self.altimeter.connect()
        if succes_altimeter:
            self.start_read_alture_bmp280()
            print("Altimeter conectado exitosamente")
        else:
            print("Altimeter no conectado")
        ## Calcule frame rate detection
        frame_rate = self.calculateFps(self.fligth_height, self.fligh_speed)
        
        if frame_rate > 1.0:
            frame_rate = 1.0
        print(".........Frame Rate:...............................", frame_rate)
        ## gps location

        self.gps_reciever.get_current_location()
        
        if self.gps_reciever.connected:
            self.start_read_location()

        self.req_fields = [ "presion",
                            "environment_temperature",  
                            "altitud_over_sea_level",
                            "altitud_over_sea_level_lib_bmp280",
                            "altitude_over_sea_level_lib_adafruit",
                            "alture",
                            "alture_lib_adafruit",
                            "alture_lib_bm280",
                            "time", 
                            "visible_image", 
                            "thermal_image", 
                            "max_temperature", 
                            "area_fire", 
                            "latitud", 
                            "longitud", 
                            "distance_xm132"]

        self.file_name = create_csv(req_fields = self.req_fields)
        #frame_rate_save = 10
        prev_time = 0
        prev_time_save = 0 
        
        while True:
            thermal_frame = self.flirone_capture.get_thermal_frame()

            ## Fire detection
           # prevTime = 0
            time_elapsed = time.time() - prev_time
            
            #prevTimeSave = 0
            time_elapsed_save = time.time() - prev_time_save

            if (time_elapsed > (1 / frame_rate)):
                print("\n\nFrame Rate:", frame_rate)
                matrix_temperatures = thermal_frame.getMatrixTemperatures()
                current_data = CURRENT_ALTIMETER_DATA.copy() 

                current_alture = current_data["alture"] if current_data["alture"] < 0.0 else 2.0

                fireDetectionOuput = self.fireForestDetector.detectFire(matrix_temperatures,current_alture, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH, 28)
                fire_prob = fireDetectionOuput.fire_prob
                fireDetectionData = fireDetectionOuput.fireDetectionData
                fireDetectionData.set_latitud(CURRENT_LOCATION["latitude"])
                fireDetectionData.set_longitud(CURRENT_LOCATION["longitude"])

                if fire_prob > 0.2:
                    self.notify_alert(fire_prob, fireDetectionData)
                    #thermal_frame.save_images()
                prev_time =  time.time()
                current_data["time"] = datetime.now()
                current_data["max_temperature"] =  fireDetectionData.max_temperature
                current_data["area_fire"] =  fireDetectionData.max_areaM2
                current_data["latitud"] = fireDetectionData.latitud
                current_data["longitud"] = fireDetectionData.longitud

            #if (time_elapsed_save > (1 / frame_rate_save)):
                print("\n\n...........................Guardando Imagenes.............................................................................\n")
                visible_image_name, thermal_image_name = thermal_frame.save_images()
                current_data["visible_image"] = f"images/{visible_image_name}.jpg"
                current_data["thermal_image"] = f"images/{thermal_image_name}.tiff"
                #prev_time_save = time.time()

                register_in_csv(self.file_name, current_data, req_fields = req_fields)
            #stop_read_radar = True
                    #break
            
            if self.show_frames:
                tframe_image = thermal_frame.getThermalFrameRGB()
            
                vframe_image = thermal_frame.getVisibleFrameRGB()
            
                cv2.namedWindow("Thermal Image", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Thermal Image", 640, 480)
                cv2.imshow("Thermal Image", tframe_image)


                cv2.namedWindow("VisibleImage", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("VisibleImage", 640, 480)
                cv2.imshow("VisibleImage", vframe_image)
                cv2.waitKey(20)
            
            thermal_frame.clear()
            del thermal_frame
            gc.collect()

    def start_read_distance(self):
        self.distanceDetector.start()
        t1 = threading.Thread(target = read_distance, args = (lambda : stop_read_radar,))
        t1.start()
  
    def start_read_location(self):
        t2 = threading.Thread(target = read_location, args = (lambda : stop_read_location, self.gps_reciever))
        t2.start()

    def start_read_alture_bmp280(self):
        t3 = threading.Thread(target = read_alture, args = (lambda : stop_read_bmp280, self.altimeter))
        t3.start()

    def notify_alert(self, alert_prob, fireDetectionOuput):
        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        data = {
            "prob": str(alert_prob),
            "maxTemperature": str(fireDetectionOuput.max_temperature),
            "areaFire": str(fireDetectionOuput.max_areaM2),
            "latitud": str(fireDetectionOuput.latitud),
            "longitud": str(fireDetectionOuput.longitud),
            "distance": str(fireDetectionOuput.fligth_height),
            "time": date_time
        }
        
        self.sio.emit("fireDetected", data)

    def calculateLongitudeVFov(self, altura):
        Vdv = 2 * altura * np.tan(0.5 * vfov * (np.pi / 180.0))

        Tdv = Vdv * SH
        return Tdv

    def calculateFps(self, altura, flightSpeed):
        dv =  self.calculateLongitudeVFov(altura)
        return  (flightSpeed  * 18/5) / ((1 - self.overlap) * dv)

def main():
    system = System(show_frames=False)
    system.run()

if __name__  == "__main__":
    main()
