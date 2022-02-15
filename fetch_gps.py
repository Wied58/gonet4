import os
import sys
import time
import smbus
import subprocess

from datetime import datetime

from gps import *

# Delay start by 15 seconds
time.sleep(15)

#os.system("sudo echo 1 > /sys/class/gpio/gpio9/value &")

# Write Headers to the log file
file = open('/home/pi/GPSLog.csv', 'a')
file.write("\n\n\n" + "CurrTimestamp" + "," + "GPSLat" + "," + "GPSLong" + "," + "GPSTime" + "," + "GPSAlt" + "," + "GPSStatus" + "\n")
file.close

gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

#x = 0

while True:
#    print (x)

    GPSLat = "0.0"
    GPSLong = "0.0"
    GPSTime = "00:00:00"
    GPSAlt = "000"
    GPSStatus = "0"

# Get timestamp
    CurrTimestamp = datetime.now()
    report = gpsd.next()

    if report['class'] == 'TPV':
        GPSLat = getattr(report,'lat',0.0)
        GPSLong = getattr(report,'lon',0.0)
        GPSTime = getattr(report,'time','')
        GPSAlt = getattr(report,'alt','nan')
        GPSMode = getattr(report,'mode','nan')
    
    if GPSLat != "0.0" and GPSLong != "0.0" and GPSAlt != "nan":
#        print("Timestamp: ", CurrTimestamp)
#        print ("Lat: ", GPSLat)
#        print ("Long: ", GPSLong)
#        print ("GPS Time: ", GPSTime)
#        print ("Altitude: ", GPSAlt)
#        print ("Mode: ", GPSMode)
        break


# Write data to a log
file = open('GPSLog.csv', 'w')
file.write(str(CurrTimestamp) + "," + str(GPSLat) + "," + str(GPSLong) + "," + str(GPSTime) + "," + str(GPSAlt) +  "\n")
file.close

#    time.sleep(0.8)
#    x += 1
