import numpy as np
import cv2
import skfuzzy as fuzz
import matplotlib.pyplot as plt

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

        #print("max_temperature:", max_temperature)
        mask_array = mask_array * 255.0
        mask_array = mask_array.astype(np.uint8)
        
        contours, hierarchy = cv2.findContours(mask_array, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        areas = []
        max_areaM2 = 0
        for cnt in contours:
            areaPixels = cv2.contourArea(cnt)
            #print("AreaPixeles:", areaPixels)
            areaM2 = self.convertAreaMeters(areaPixels, fligth_height, height, width)
            if areaM2 > max_areaM2:
                max_areaM2 = areaM2
            #print("areaM2:", areaM2)

        #print("max_areaM2:", max_areaM2)
        alert_prob = self.fuzzy_system_inference(max_temperature,max_areaM2)
        return alert_prob, max_areaM2, max_temperature
         
    def init_fuzzy_system(self):
        ## Generando las variables
        self.x_temperature = np.arange(0,200,1)
        self.x_areaFire = np.arange(0,20,0.5)
        self.x_alert = np.arange(0,1,0.1)

        ## Fuzzy member ship
        self.temp_low = fuzz.trapmf(self.x_temperature, [0, 0, 30, 50])
        self.temp_medium = fuzz.trapmf(self.x_temperature, [30, 50, 80, 100])
        self.temp_high = fuzz.trimf(self.x_temperature,[80,100,120])
        self.temp_very_high = fuzz.trapmf(self.x_temperature,[100,120,200,200])

        self.areaF_very_low = fuzz.trapmf(self.x_areaFire, [0, 0, 0.5, 1.5])
        self.areaF_low = fuzz.trimf(self.x_areaFire, [0.5, 1.5, 2.5])
        self.areaF_medium = fuzz.trimf(self.x_areaFire, [1.5, 2.5, 5])
        self.areaF_high = fuzz.trimf(self.x_areaFire, [2.5, 5, 10])
        self.areaF_very_high = fuzz.trapmf(self.x_areaFire, [5, 10, 20, 20])

        self.alert_low = fuzz.trapmf(self.x_alert, [0,0, 0.3 ,0.5])
        self.alert_medium = fuzz.trimf(self.x_alert, [0.3, 0.5 , 0.7])
        self.alert_high = fuzz.trapmf(self.x_alert, [0.5,0.7, 1.0,1.0])

    def fuzzy_inference(self, temperature, areaFire):
        temp_level_low = fuzz.interp_membership(self.x_temperature, self.temp_low, temperature) 
        temp_level_medium = fuzz.interp_membership(self.x_temperature, self.temp_medium, temperature) 
        temp_level_high = fuzz.interp_membership(self.x_temperature, self.temp_high, temperature) 
        temp_level_very_high = fuzz.interp_membership(self.x_temperature, self.temp_very_high, temperature)

        areaF_level_very_low = fuzz.interp_membership(self.x_areaFire, self.areaF_low, areaFire) 
        areaF_level_low = fuzz.interp_membership(self.x_areaFire, self.areaF_very_low, areaFire) 
        areaF_level_medium = fuzz.interp_membership(self.x_areaFire, self.areaF_medium, areaFire) 
        areaF_level_high = fuzz.interp_membership(self.x_areaFire, self.areaF_high, areaFire) 
        areaF_level_very_high = fuzz.interp_membership(self.x_areaFire, self.areaF_very_high, areaFire) 

        ## Primera regla
        ## Rule Verde
        rule1_1 = np.fmin(temp_level_low, areaF_level_very_low)
        rule1_2 = np.fmin(temp_level_low, areaF_level_low)
        rule1_3 = np.fmin(temp_level_low, areaF_level_medium)
        rule1_4 = np.fmin(temp_level_low, areaF_level_high)
        rule1_5 = np.fmin(temp_level_medium, areaF_level_very_low)
        
        rule1_6 = np.fmax(rule1_1, rule1_2)
        rule1_7 = np.fmax(rule1_3, rule1_4)
        rule1_8 = np.fmax(rule1_5, rule1_6)
        rule_verde = np.fmax(rule1_7, rule1_8)

        ## Rule Naranja

        rule2_1 = np.fmin(temp_level_medium, areaF_level_low)
        rule2_2 = np.fmin(temp_level_medium, areaF_level_medium)
        rule2_3 = np.fmin(temp_level_medium, areaF_level_high)
        rule2_4 = np.fmin(temp_level_medium, areaF_level_very_high)

        rule2_5 = np.fmin(temp_level_high, areaF_level_very_low)
        rule2_6 = np.fmin(temp_level_high, areaF_level_low)
        rule2_7 = np.fmin(temp_level_high, areaF_level_medium)
        
        rule2_8 = np.fmin(temp_level_very_high, areaF_level_very_low)
        rule2_9 = np.fmin(temp_level_very_high, areaF_level_low)

        rule2_10 =  np.fmax(rule2_1, rule2_2)
        rule2_11 =  np.fmax(rule2_3, rule2_4)
        rule2_12 =  np.fmax(rule2_5, rule2_6)
        rule2_13 =  np.fmax(rule2_7, rule2_8)

        rule2_14 =  np.fmax(rule2_9, rule2_10)
        rule2_15 =  np.fmax(rule2_11, rule2_12)
        rule2_16 =  np.fmax(rule2_13, rule2_14)

        rule_naranja =  np.fmax(rule2_15, rule2_16)

        ## Rule Rojo

        rule3_1 = np.fmin(temp_level_high, areaF_level_high)
        rule3_2 = np.fmin(temp_level_high, areaF_level_very_high)
        rule3_3 = np.fmin(temp_level_very_high, areaF_level_medium)
        rule3_4 = np.fmin(temp_level_very_high, areaF_level_high)
        rule3_5 = np.fmin(temp_level_very_high, areaF_level_very_high)
        
        rule3_6 = np.fmax(rule3_1,rule3_2)
        rule3_7 = np.fmax(rule3_3,rule3_4)
        rule3_8 = np.fmax(rule3_5,rule3_6)

        rule_rojo = np.fmax(rule3_7,rule3_8)

        #print("verde:", rule_verde)
        #print("naranja:", rule_naranja)
        #print("rojo:", rule_rojo)
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
        
        #print("Prob Alert:", prob_alert)

        return FuzzyOutput(prob_alert, rule_verde, rule_naranja, rule_rojo)
    
    def fuzzy_system_inference(self, maxTemperature, areaFire):
        rule_verde, rule_naranja , rule_rojo = self.fuzzy_inference(maxTemperature, areaFire)
        return self.defuzzification(rule_verde, rule_naranja , rule_rojo)

    def plot(self):
        ## Visualize memberships
        fig, (ax0, ax1, ax2) = plt.subplots(nrows= 3, figsize = (8,9))

        ax0.plot(self.x_temperature, self.temp_low, 'b', linewidth = 1.5, label = 'Baja')
        ax0.plot(self.x_temperature, self.temp_medium, 'g', linewidth = 1.5, label = 'Media')
        ax0.plot(self.x_temperature, self.temp_high, 'orange', linewidth = 1.5, label = 'Alta')
        ax0.plot(self.x_temperature, self.temp_very_high, 'r', linewidth = 1.5, label = 'Muy Alta')

        ax0.set_title('Temperature')
        ax0.legend()

        
        
        ax1.plot(self.x_areaFire, self.areaF_very_low, 'b', linewidth = 1.5, label = 'Muy Bajo')
        ax1.plot(self.x_areaFire, self.areaF_low, 'c', linewidth = 1.5, label = 'Bajo')
        ax1.plot(self.x_areaFire, self.areaF_medium, 'g', linewidth = 1.5, label = 'Medio')
        ax1.plot(self.x_areaFire, self.areaF_high, 'y', linewidth = 1.5, label = 'Alto')
        ax1.plot(self.x_areaFire, self.areaF_very_high, 'r', linewidth = 1.5, label = 'Muy Alto')
        ax1.set_xticks(range(0,21, 1))
        ax1.set_title('Area')
        ax1.legend()

        #ax2.plot(self.x_alert, self.alert_low, 'g', linewidth = 1.5, label = 'Verde')
        #ax2.plot(self.x_alert, self.alert_medium, 'y', linewidth = 1.5, label = 'Amarillo')
        #ax2.plot(self.x_alert, self.alert_high, 'r', linewidth = 1.5, label = 'Rojo')
        ax2.vlines(0.2, 0, 1, 'g', linewidth = 1.5, label = 'Verde')
        ax2.vlines(0.5, 0, 1, 'y', linewidth = 1.5, label = 'Amarillo')
        ax2.vlines(1.0, 0, 1, 'r', linewidth = 1.5, label = 'Rojo')
        ax2.set_title('Nivel de Alerta')
        ax2.legend()

        # Turn off top/right axes
        for ax in (ax0, ax1, ax2):
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.get_xaxis().tick_bottom()
            ax.get_yaxis().tick_left()
        plt.tight_layout()  
        plt.show()

if __name__ == "__main__":
    maxTemperature = 100
    area_region_m2 = 5.0
    fuzzySystem = FuzzySystem()
    fuzzySystem.plot()
    rule_verde, rule_naranja , rule_rojo = fuzzySystem.fuzzy_inference(maxTemperature, area_region_m2)
    print("rule_verde:", rule_verde)
    print("rule_naranja:", rule_naranja)
    print("rule_rojo:", rule_rojo)
    output = fuzzySystem.defuzzification(rule_verde, rule_naranja , rule_rojo)
    print("output.alert_prob: ",output.alert_prob)
    ## Ecuaciones.
    