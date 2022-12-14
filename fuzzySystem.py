import numpy as np
import cv2
import skfuzzy as fuzz

SH = 0.6136
SW = 0.620
hfov = 38
vfov = 50

class FuzzyOutput:
    def __init__(self, alert_prob, membership_alert_green, membership_alert_orange,  membership_alert_red):
        self.alert_prob = alert_prob
        self.membership_alert_green = membership_alert_green
        self.membership_alert_orange = membership_alert_orange
        self.membership_alert_red = membership_alert_red

class FuzzySystem:
    def __init__(self) -> None:
        self.init_fuzzy_system()

    def detectFire(self, M_Temperatures, fligth_height, height, width, threshold_temperature = 100):
        max_temperature = M_Temperatures.max()
        mask_array = M_Temperatures > threshold_temperature

        print("max_temperature:", max_temperature)
        mask_array = mask_array * 255.0
        mask_array = mask_array.astype(np.uint8)
        
        contours, hierarchy = cv2.findContours(mask_array, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        areas = []
        max_areaM2 = 0
        for cnt in contours:
            areaPixels = cv2.contourArea(cnt)
            print("AreaPixeles:", areaPixels)
            areaM2 = self.convertAreaMeters(areaPixels, fligth_height, height, width)
            if areaM2 > max_areaM2:
                max_areaM2 = areaM2
            print("areaM2:", areaM2)

        print("max_areaM2:", max_areaM2)
        alert_prob = self.fuzzy_system_inference(max_temperature,max_areaM2)
        return alert_prob, max_areaM2, max_temperature
         
    def init_fuzzy_system(self):
        ## Generando las variables
        self.x_temperature = np.arange(0,300,1)
        self.x_areaFire = np.arange(0,20,0.5)
        self.x_alert = np.arange(0,1,0.1)

        ## Fuzzy member ship
        self.temp_low = fuzz.trapmf(self.x_temperature, [0, 0,50, 100])
        self.temp_medium = fuzz.trimf(self.x_temperature, [50, 100, 140])
        self.temp_high = fuzz.trapmf(self.x_temperature,[80,140,300,300])

        self.areaF_low = fuzz.trapmf(self.x_areaFire, [0, 0, 0.5, 1])
        self.areaF_medium = fuzz.trimf(self.x_areaFire, [0.5, 1, 2])
        self.areaF_high = fuzz.trapmf(self.x_areaFire, [1, 2, 20,20])

        self.alert_low = fuzz.trapmf(self.x_alert, [0,0, 0.3 ,0.5])
        self.alert_medium = fuzz.trimf(self.x_alert, [0.3, 0.5 , 0.7])
        self.alert_high = fuzz.trapmf(self.x_alert, [0.5,0.7, 1.0,1.0])

    def fuzzy_inference(self, temperature, areaFire):
        temp_level_low = fuzz.interp_membership(self.x_temperature, self.temp_low, temperature) 
        temp_level_medium = fuzz.interp_membership(self.x_temperature, self.temp_medium, temperature) 
        temp_level_high = fuzz.interp_membership(self.x_temperature, self.temp_high, temperature) 

        areaF_level_low = fuzz.interp_membership(self.x_areaFire, self.areaF_low, areaFire) 
        areaF_level_medium = fuzz.interp_membership(self.x_areaFire, self.areaF_medium, areaFire) 
        areaF_level_high = fuzz.interp_membership(self.x_areaFire, self.areaF_high, areaFire) 

        ## Primera regla
        ## Rule Verde
        rule1_1 = np.fmin(temp_level_low, areaF_level_low)
        rule1_2 = np.fmin(temp_level_low, areaF_level_medium)
        rule1_3 = np.fmin(temp_level_low, areaF_level_high)
        rule1_4 = np.fmin(temp_level_medium, areaF_level_low)
        rule1_5 = np.fmax(rule1_1, rule1_2)
        rule1_6 = np.fmax(rule1_3, rule1_4)

        rule_verde = np.fmax(rule1_5, rule1_6)

        ## Rule Naranja

        rule2_1 = np.fmin(temp_level_medium, areaF_level_medium)
        rule2_2 = np.fmin(temp_level_medium, areaF_level_high)
        rule2_3 = np.fmin(temp_level_high, areaF_level_low)
        rule2_4 =  np.fmax(rule2_1, rule2_2)
        rule_naranja =  np.fmax(rule2_4, rule2_3)

        ## Rule Naranja

        rule3_1 = np.fmin(temp_level_high, areaF_level_medium)
        rule3_2 = np.fmin(temp_level_high, areaF_level_high)
        rule_rojo = np.fmax(rule3_1,rule3_2)

        return rule_verde, rule_naranja , rule_rojo
    
    def defuzzification(self, rule_verde, rule_naranja , rule_rojo):
        ## Desfuzificacion
            #verde = np.fmin(rule_verde, self.alert_low)
            #naranja = np.fmin(rule_naranja, self.alert_medium)
            #rojo = np.fmin(rule_rojo, self.alert_high) 
            #aggregated = np.fmax(verde, np.fmax(naranja, rojo))
        
        x_values = [0.2, 0.5, 1.0]
        #prob_alert = fuzz.defuzz(self.x_alert, aggregated, 'centroid')
        # Calculate defuzzified result
        prob_alert = (rule_verde * x_values[0] + rule_naranja * x_values[1] + rule_rojo * x_values[2]) / (rule_verde + rule_naranja + rule_rojo)

        return FuzzyOutput(prob_alert, rule_verde, rule_naranja, rule_rojo)
    
    def fuzzy_system_inference(self, maxTemperature, areaFire):
        rule_verde, rule_naranja , rule_rojo = self.fuzzy_inference(maxTemperature, areaFire)
        return self.defuzzification(rule_verde, rule_naranja , rule_rojo)
