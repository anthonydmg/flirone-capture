from gps import *
import time

running = True

class GPS_RECEIVER():
    def __init__(self):
        self.gpds = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        self.connected  = True
        self.get_current_location()

    def get_current_location(self):
        try:
            if self.connected:
                nx = self.gpds.next()
                if nx['class'] == 'TPV':
                    latitude = getattr(nx,'lat', "Unknown")
                    longitude = getattr(nx,'lon', "Unknown")
                    print ("Your position: lon = " + str(longitude) + ", lat = " + str(latitude))
                location = { 
                    "latitude" : latitude,
                    "longitude": longitude}
                return location
            else: 
                return {"latitude": "", "longitude": ""}
        except:
            print("GPS no conectado..")
            self.connected = False
            return {"latitude": "", "longitude": ""}
