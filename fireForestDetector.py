import numpy as np
import cv2
from fuzzySystem import FuzzySystem

SH = 0.6136
SW = 0.620
hfov = 38
vfov = 50
THERMAL_IMAGE_HEIGTH = 80
THERMAL_IMAGE_WIDTH = 60

class FireDetecionData:
    def __init__(self, max_temperature, max_areaM2, latitud = "", longitud =  "", fligth_height =  10.0):
        self.max_areaM2 = max_areaM2
        self.max_temperature = max_temperature
        self.latitud = "",
        self.longitud = ""
        self.fligth_height = fligth_height
    
    def set_max_area(self, max_areaM2):
        self.max_areaM2 = max_areaM2

    def set_max_temperature(self, max_temperature):
        self.max_temperature = max_temperature

    def set_latitud(self, latitud):
        self.latitud = latitud

    def set_longitud(self, longitud):
        self.longitud = longitud
    
    def set_fligth_height(self, fligth_height):
        self.fligth_height = fligth_height
    

class FireDetectionOuput:
    def __init__(self, fire_prob, alert_level, max_temperature, max_areaM2, fligth_height):
        self.fire_prob = fire_prob
        self.alert_level = alert_level
        self.fireDetectionData = FireDetecionData(max_temperature, max_areaM2, fligth_height)

class FireForestDetector:
    def __init__(self):
          self.fuzzy_system = FuzzySystem()
    def find_hot_regions(self, Matrix_Temperatures, threshold_temperature):
        mask_array = Matrix_Temperatures > threshold_temperature
        mask_array = mask_array * 255.0
        mask_array = mask_array.astype(np.uint8)
        contours, hierarchy = cv2.findContours(mask_array, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def calculate_largest_area(self, hot_regions_contours, fligth_height):
        #areas = []
        max_areaM2 = 0
        for cnt in hot_regions_contours:
            areaPixels = cv2.contourArea(cnt)
            print("AreaPixeles:", areaPixels)
            areaM2 = self.convertAreaMeters(areaPixels, fligth_height, THERMAL_IMAGE_HEIGTH, THERMAL_IMAGE_WIDTH)
            if areaM2 > max_areaM2:
                max_areaM2 = areaM2
            print("areaM2:", areaM2)
        return max_areaM2
    
    def calcule_max_temperature(self, Matrix_Temperatures):
        max_temperature = Matrix_Temperatures.max()

    def detectFire(self, Matrix_Temperatures, fligth_height, height, width, threshold_temperature = 100):
        hot_regions_contours = self.find_hot_regions(Matrix_Temperatures, threshold_temperature)
        max_areaM2 = self.calculate_largest_area(hot_regions_contours, fligth_height)
        max_temperature = self.calcule_max_temperature(Matrix_Temperatures)
        fuzzyOutput = self.fuzzy_system.fuzzy_system_inference(max_temperature, max_areaM2)
        
        fire_prob = fuzzyOutput.alert_prob
        
        if fuzzyOutput.membership_alert_orange > 0.5:
            alert_level = "orange"
        else:
            alert_level = "red"

        fireDetectionOuput = FireDetectionOuput(fire_prob, alert_level, max_temperature, max_areaM2 , fligth_height)

        return fireDetectionOuput
   
    def convertAreaMeters(self, areaPixels,  altura,  heigth,  width):
        # RGB images distances
        # print("areaPixels:", areaPixels)
        Vdh = 2 * altura * np.tan(0.5 * hfov * (np.pi/ 180.0))
        Vdv = 2 * altura * np.tan(0.5 * vfov * (np.pi/ 180.0))
        # Scale to thermal distances
        Tdh = Vdh * SH
        Tdv = Vdv * SW
        print("area Image:", Tdv * Tdh)
        pixelSize = (Tdv * Tdh) / (heigth * width)
        areaMeters = areaPixels * pixelSize
        return areaMeters