import ctypes

clibrary = ctypes.CDLL("./ejemploctypes/cpplibrary.so")

from ctypes import *

jpg_size = ctypes.c_uint32()
thermal_size = ctypes.c_uint32()
payload_size = ctypes.c_uint32()
tframe_data = (ctypes.c_uint8 * 350000)()
gray16frame = (ctypes.c_uint16 * 4800)()
minval_gray = ctypes.c_uint16()
maxval_gray = ctypes.c_uint16()