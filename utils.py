import csv
from datetime import datetime
import time
import os
#data = { "presion": 101451, "alture": 100 , "altitud_sobre_nivel_mar": 1010, "hora":  datetime.now()}

#req_fields = ["presion", "alture", "altitud_sobre_nivel_mar", "hora"]

#def creat_csv():

#with open("output.csv", "a", newline= "") as f_output:
#    cv_output = csv.DictWriter(f_output, fieldnames = req_fields)
#    cv_output.writeheader()
#    cv_output.writerow(data)

class StreamingMovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.values = []
        self.sum = 0

    def process(self, value):
        self.values.append(value)
        self.sum += value
        if len(self.values) > self.window_size:
            self.sum -= self.values.pop(0)
        return float(self.sum) / len(self.values)

def create_csv(name_base = "fire_detection_",req_fields = ["presion", "alture", "alture_over_sea_level", "time", "visible_image", "thermal_image"]):
    dir_path = "./registers"
    os.makedirs(dir_path, exist_ok= True)
    now = datetime.now()
    date_time_str = now.strftime("%Y_%m_%d_%H_%M_%S_%f")
    file_name = f"{dir_path}/{name_base}{date_time_str}.csv"
    with open(file_name, "a", newline= "") as f_output:
        cv_output = csv.DictWriter(f_output, fieldnames = req_fields)
        cv_output.writeheader()
    print(date_time_str)
    return file_name

def register_in_csv(name_file, data ,req_fields = ["presion", "alture", "alture_over_sea_level", "time", "visible_image", "thermal_image"]):
    with open(name_file, "a", newline= "") as f_output:
        cv_output = csv.DictWriter(f_output, fieldnames = req_fields)
        cv_output.writerow(data)
