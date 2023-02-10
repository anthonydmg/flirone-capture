from gps import *
import time

class GPS_RECEIVER:
    def __init__(self):
        self.gpds = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        self.connected  = True
        #time.sleep(1.0)
        #self.get_current_location()

    def get_current_location(self):
        try:
            if self.connected == True:
                nx = self.gpds.next()
                print(nx)
                if nx['class'] == 'TPV':
                    latitude = getattr(nx,'lat', "Unknown")
                    longitude = getattr(nx,'lon', "Unknown")
                    print ("Your position: lon = " + str(longitude) + ", lat = " + str(latitude))
                    location = { 
                        "latitude" : latitude,
                        "longitude": longitude}
                    
                    return location
                return {"latitude": "", "longitude": ""}
            else: 
                return {"latitude": "", "longitude": ""}
        except Exception as error:
            print("GPS no conectado..")
            print(error)
            self.connected = False
            return {"latitude": "", "longitude": ""}


if __name__ == "__main__":
    gps_reciever = GPS_RECEIVER()
    CURRENT_LOCATION = {"latitude": "", "longitude": ""}

    def read_location(stop_read_location, gps_reciever):
        while True:
            print("Thread runing Location")
            location = gps_reciever.get_current_location()
            print("Location: ", location)
            if location["latitude"]!= "" and location["longitude"]!= "":
                CURRENT_LOCATION = location
            time.sleep(0.3)
            if stop_read_location():
                distanceDetector.close()
                break
    
        
    stop_read_location = False

    def start_read_location():
        import threading
        
        t2 = threading.Thread(target = read_location, args = (lambda : stop_read_location, gps_reciever))
        t2.start()

    gps_reciever.get_current_location()
    print(gps_reciever.connected)   
    if gps_reciever.connected:
            start_read_location()