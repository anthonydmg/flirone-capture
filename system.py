import ctypes
from ctypes import *
import numpy as np
import cv2
from fuzzySystem import FuzzySystem
import socketio
from datetime import datetime
import time
from flirone_capture import FlirOneCapture

from module_radar import ModuleDistanceDetector
import threading
from fireForestDetector import FireForestDetector, FireDetecionData, FireDetectionOuput
sio = socketio.Client()

FRAME_RATE = 2

THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60

INIT_FLIGHT_HEIGHT = 10
INIT_FLIGHT_SPEED = 30
stop_read_radar = False
SH = 0.6136
SW = 0.620
hfov = 38
vfov = 50

def read_distance(stop_read):
    while True:
        print("Thread runing")
        distance = distanceDetector.read()
        if distance != 0:
            fligth_height = distance
            frameRate = calculateFps(fligth_height)
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

    def run(self):
        opened = self.flirone_capture.open_device()

        if opened:
         print("Dispositivo conectado existosamente")
        else:
            print("Ocurrio un error al memento de abrir dispositivo")
            exit(0)

        #self.sio.connect('http://localhost:5055')
        #self.sio.emit("startFireDetection", "Comienzar Detecction")

        success = self.distanceDetector.connect()

        if success:
            print("XM132 conectado exitosamente")
            self.start_read_distance()
        else:
            print("XM132 no se puedo conectar")

        frame_rate = self.calculateFps(self.fligth_height, self.fligh_speed)


        while True:
            thermal_frame = self.flirone_capture.get_thermal_frame()

            ## Fire detection
            prevTime = 0
            time_elapsed = time.time() - prevTime
            
            if (time_elapsed > (1 / frame_rate)):
                matrix_temperatures = thermal_frame.getMatrixTemperatures()
                
                fireDetectionOuput = self.fireForestDetector.detectFire(matrix_temperatures, self.fligth_height, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH)
                
                if fireDetectionOuput.fire_prob > 0.5:
                    fireDetectionData = fireDetectionOuput.fireDetectionData
                    
                    notify_alert(fireDetectionData)

                    thermal_frame.save_images()
                    stop_read_radar = True
                    break
                #sio.emit("fireDetected", data)
            
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


        

    
    def start_read_distance(self):
        self.distanceDetector.start()
        t1 = threading.Thread(target = read_distance, args = (lambda : stop_read_radar,))
        t1.start()
       
    def notify_alert(self, fireDetectionOuput):
        now = datetime.now() # current date and time
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        data = {
            "maxTemperature": str(fireDetectionOuput.max_temperature),
            "areaFire": str(fireDetectionOuput.max_areaM2),
            "latitud": "0",
            "longitud": "0",
            "distance": str(fireDetectionOuput.fligth_height),
            "time": date_time
        }

        print("Fuego encontrado!!:", data) 
        
        #self.sio.emit("fireDetected", data)

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