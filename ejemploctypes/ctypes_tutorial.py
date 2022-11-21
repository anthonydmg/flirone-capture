import ctypes
import numpy as np
clibrary = ctypes.CDLL("./ejemploctypes/cpplibrary.so")

from ctypes import *

""" class ThermalFrame:
    def __init__(self):
        jpg_size = 0
        thermal_size = 0
        payload_size = 0
        
    def set_gray16frame(self, array):
        self.gray16frame = array """

jpg_size = ctypes.c_uint32()
thermal_size = ctypes.c_uint32()
payload_size = ctypes.c_uint32()
tframe_data = (ctypes.c_uint8 * 350000)()
gray16frame = (ctypes.c_uint16 * 4800)()
minval_gray = ctypes.c_uint16()
maxval_gray = ctypes.c_uint16()

#clibrary.read_tframe.argtypes = [POINTER(ctypes.c_uint8), POINTER(ctypes.c_uint32), POINTER(ctypes.c_uint32),POINTER(ctypes.c_uint32)]

clibrary.read_tframe(tframe_data , byref(jpg_size), byref(thermal_size), byref(payload_size))

#print(tframe_data[0])

clibrary.read_gray16_scale.argtypes = [ POINTER(ctypes.c_uint8),
                                        POINTER(ctypes.c_uint16), 
                                        POINTER(ctypes.c_uint32),
                                        POINTER(ctypes.c_uint16),
                                        POINTER(ctypes.c_uint16)
                                        ]

clibrary.read_gray16_scale(tframe_data, gray16frame, byref(jpg_size), byref(minval_gray), byref(maxval_gray))

#uint8_t tframe_data[350000], uint16_t gray16frame [4800], uint32_t  &thermal_size, uint32_t  &minval_gray, uint32_t  &maxval_gray
print(tframe_data[0])
print(gray16frame)
print(gray16frame[0])
print(gray16frame[1])

x = np.ones((3,3), dtype= np.float)


print(x)

clibrary.my_func.restype = None
clibrary.my_func.argtypes = [np.ctypeslib.ndpointer(dtype = np.float, ndim=2, flags='C_CONTIGUOUS')]
clibrary.my_func(x)

print(x)

""" clibrary.read_tframe.argtypes[
    np.ctypeslib.ndpointer(dtype = np.int, ndim=3, flags='C_CONTIGUOUS')
    ]

clibrary.read_tframe(gray16frame, ctypes.byref(jpg_size), ctypes.byref(thermal_size), ctypes(payload_size))
 """
""" 
class ThermalFrame(Structure):
    _fields_ = [
       ("jpg_size", c_uint32),
       ("thermal_size", c_uint32),
       ("pyload_size", c_uint32),
       ("gray16frame", np.ctypeslib.ndpointer(dtype = np.int, ndim=3, flags='C_CONTIGUOUS')),
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.gray16frame = np.zeros((80,60)) """



#np.zeros((80,60,3), dtype= np.int)
""" tframe = ThermalFrame()
clibrary.tframe_size(ctypes.byref(tframe))
 """
#clibrary.tframe_size(ctypes.byref(tframe))
#print(tframe.jpg_size)
""" 
    uint32_t jpg_size = 0;
    uint32_t thermal_size = 0;
    uint32_t pyload_size = 0;
    uint32_t pointer = 0;
    const int32_t TFRAME_WIDTH = 80;
    const int32_t TFRAME_HEIGHT = 60;
    const int32_t VISUAL_WIDTH = 640;
    const int32_t VISUAL_HEIGHT = 480;
    const int32_t TFRAME_SIZE=(4800);
    const int32_t COLOR_IMAGE_SIZE=(VISUAL_WIDTH*VISUAL_HEIGHT);
    uint8_t buffer_data[350000];
    uint8_t * palette_colormap;
    bool complete = false;
    uint16_t TFrameGray16[80][60];
    uint16_t maxval_gray = 0;
    uint16_t minval_gray = 65536;
    uint16_t max_x = 0;
    uint16_t max_y = 0;
    /* data */

x = np.ones((3,3,3), dtype= np.float)


print(x)

clibrary.my_func.restype = restype = None
clibrary.my_func.argtypes = [np.ctypeslib.ndpointer(dtype = np.float, ndim=3, flags='C_CONTIGUOUS')]
clibrary.my_func(x)

print(x)
 """