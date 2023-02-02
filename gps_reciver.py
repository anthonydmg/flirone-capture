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
    gps_receiver = GPS_RECEIVER()
    location = gps_receiver.get_current_location()
    print(location)