import ctypes
from ctypes import *
import numpy as np
import os
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

class ThermalFrame:
    def __init__(self, jpg_size, thermal_size, payload_size , tframe_data ):
        self.jpg_size = jpg_size
        self.thermal_size = thermal_size
        self.payload_size = payload_size
        self.tframe_data = tframe_data
        self.gray16frame = None
        self.vframe_color = None
        self.tframe_color = None
        self.minval_gray = ctypes.c_uint16()
        self.maxval_gray = ctypes.c_uint16()

    def get_thermal_frame_16_bits(self):
        self.gray16frame = (ctypes.c_uint16 * (THERMAL_IMAGE_HEIGTH * THERMAL_IMAGE_WIDTH))()

        cflironecapture.read_gray16_scale.argtypes = [ POINTER(ctypes.c_uint8),
                                            POINTER(ctypes.c_uint16), 
                                            POINTER(ctypes.c_uint32),
                                            POINTER(ctypes.c_uint16),
                                            POINTER(ctypes.c_uint16)
                                            ]

        cflironecapture.read_gray16_scale(self.tframe_data, self.gray16frame, byref(self.jpg_size), byref(self.minval_gray), byref(self.maxval_gray))
    
    def getMatrixTemperatures(self):
        if self.gray16frame == None:
            self.get_thermal_frame_16_bits()

        self.temperatures = (ctypes.c_double *  (THERMAL_IMAGE_HEIGTH * THERMAL_IMAGE_WIDTH))()

        cflironecapture.read_tframe_temperatures.argtypes = [
                                        POINTER(ctypes.c_uint16), 
                                        POINTER(ctypes.c_double),
                                        ]

        cflironecapture.read_tframe_temperatures(self.gray16frame, self.temperatures)

        matrix_temperatures = np.array(self.temperatures, dtype= np.float32)
        matrix_temperatures = matrix_temperatures.reshape(80, 60)
        return matrix_temperatures
    
    def getThermalFrameRGB(self):
        if self.gray16frame == None:
            self.get_thermal_frame_16_bits()

        self.tframe_color = (ctypes.c_uint8 * (THERMAL_IMAGE_HEIGTH * THERMAL_IMAGE_WIDTH* 3))()

        cflironecapture.read_tframe_color.argtypes = [ POINTER(ctypes.c_uint16), 
                                                POINTER(ctypes.c_uint8),
                                                POINTER(ctypes.c_uint16),
                                                POINTER(ctypes.c_uint16)
                                                ]
        cflironecapture.read_tframe_color(self.gray16frame, self.tframe_color , byref(self.minval_gray), byref(self.maxval_gray))

        tframe_image = np.array(self.tframe_color, dtype= np.uint8)
        tframe_image = tframe_image.reshape((THERMAL_IMAGE_HEIGTH,THERMAL_IMAGE_WIDTH,3))
        return tframe_image


    def getVisibleFrameRGB(self):
        if self.gray16frame == None:
            self.get_thermal_frame_16_bits()

        self.vframe_color = (ctypes.c_uint8 * (VISIBLE_IMAGE_HEIGTH * VISIBLE_IMAGE_WIDTH * 3))()

        cflironecapture.read_frame_color.argtypes = [
                                        POINTER(ctypes.c_uint8),
                                        POINTER(ctypes.c_uint8),
                                        POINTER(ctypes.c_uint32),
                                        POINTER(ctypes.c_uint32),
                                        ctypes.c_uint32,
                                        ctypes.c_uint32
                                    ]
        ret = cflironecapture.read_frame_color(self.tframe_data, self.vframe_color, self.thermal_size, self.jpg_size, VISIBLE_IMAGE_HEIGTH, VISIBLE_IMAGE_WIDTH)
        if ret :
            Vframe_image = np.array(self.vframe_color, dtype= np.uint8)
            Vframe_image = Vframe_image.reshape((VISIBLE_IMAGE_HEIGTH,VISIBLE_IMAGE_WIDTH,3))
        else:
            print("Ocurrio un error al obtener la imagen de la camara RGB")
            Vframe_image = np.zeros((VISIBLE_IMAGE_HEIGTH,VISIBLE_IMAGE_WIDTH, 3))

        return Vframe_image

    def save_images(self, path_file = "./images"):
        os.makedirs(path_file, exist_ok = True)
        
        path_file = path_file.encode("utf-8")
        path_char = (ctypes.c_char * 100)(*path_file)

        if self.gray16frame == None:
            self.get_thermal_frame_16_bits()

        if self.vframe_color == None:
            self.getVisibleFrameRGB()

        cflironecapture.save_flirone_images(path_char, self.gray16frame, THERMAL_IMAGE_WIDTH, THERMAL_IMAGE_HEIGTH, self.vframe_color, VISIBLE_IMAGE_WIDTH, VISIBLE_IMAGE_HEIGTH)

class FlirOneCapture:
    def __init__(self):
        #Init variables 
        self.jpg_size = ctypes.c_uint32()
        self.thermal_size = ctypes.c_uint32()
        self.payload_size = ctypes.c_uint32()
        self.tframe_data = (ctypes.c_uint8 * BUFFER_SIZE)()
        self.gray16frame = (ctypes.c_uint16 * (THERMAL_IMAGE_HEIGTH * THERMAL_IMAGE_WIDTH))()
        self.temperatures = (ctypes.c_double *  (THERMAL_IMAGE_HEIGTH * THERMAL_IMAGE_WIDTH))()


    def open_device(self):
        device_handle = cflironecapture.open_device()
        if device_handle:
            self.device_handle = device_handle
            return True
        else:
            return False

    def read_frame_data(self):
        cflironecapture.read_tframe(self.device_handle, self.tframe_data , byref( self.jpg_size), byref(self.thermal_size), byref(self.payload_size))
      

    def close_device(self):
        pass
    
    def get_thermal_frame(self):
        self.read_frame_data()
        # New Frame
        thermal_frame = ThermalFrame(self.jpg_size, self.thermal_size, self.payload_size , self.tframe_data)
        return thermal_frame
    


