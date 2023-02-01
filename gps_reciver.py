from gps import *
import time

running = True

class GPS_RECEIVER():
    def __init__(self):
        self.gpds = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
    
    def get_current_location():
        nx = gpsd.next()
        if nx['class'] == 'TPV':
            latitude = getattr(nx,'lat', "Unknown")
            longitude = getattr(nx,'lon', "Unknown")
            print ("Your position: lon = " + str(longitude) + ", lat = " + str(latitude))
        location = { 
            "latitude" : latitude,
            "longitude": longitude}
        return location