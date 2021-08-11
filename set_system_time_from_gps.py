# Here date and time is captured from GPS $GPRMC if available.
# The time service from the network is shutdown, and system time is set from GPS value.
# Then the network time service is restarted in case the device is being tested indoors
# and network is accessible and GPS is not. 
#
# This is in case the program is executed without access to netork.
# It is ran everytime the program is executed in case GPS is not valid when the GONet
# device is first turned on. 
#

import serial
import subprocess
import syslog
import time 


port = "/dev/serial0"
ser = serial.Serial(port, baudrate = 9600, timeout = 0.5)

print ("The sysdate at startup is: ")
subprocess.call('date')


i = 0
while i < 5:
   time.sleep(1.0)
   data = ser.read_until().decode('utf_8') 
   sdata = data.split(",")
   if sdata[0] == '$GPRMC' and sdata[2] == 'V':
        print (sdata)
   elif sdata[0] == '$GPRMC' and sdata[2] != 'V':

        sdate = sdata[9]
        stime = sdata[1]
        
        if   sdate[2:4] == '01':
        	smonth = "JAN"
        elif sdate[2:4] == '02':
        	smonth = "FEB"
        elif sdate[2:4] == '03':
        	smonth = "MAR"
        elif sdate[2:4] == '04':
        	smonth = "APR"
        elif sdate[2:4] == '05':
        	smonth = "MAY"
        elif sdate[2:4] == '06':
        	smonth = "JUN"
        elif sdate[2:4] == '07':
        	smonth = "JUL"
        elif sdate[2:4] == '08':
        	smonth = "AUG"
        elif sdate[2:4] == '09':
        	smonth = "SEP"
        elif sdate[2:4] == '10':
        	smonth = "OCT"
        elif sdate[2:4] == '11':
        	smonth = "NOV"
        elif sdate[2:4] == '12':
        	smonth = "DEC"
        
        print (sdate[0:2] + " " + smonth + " " +"20"+ sdate[4:7] + " " + stime[0:2] + ":" + stime[2:4] + ":" + stime[4:6])
        date_time = sdate[0:2] + " " + smonth + " " +"20"+ sdate[4:7] + " " + stime[0:2] + ":" + stime[2:4] + ":" + stime[4:6]
        
        print ("Shutting down network time service")
        command = ['sudo', 'systemctl', 'stop', 'systemd-timesyncd.service']
        subprocess.call(command)
        
        print("The sysdate before setting with GPS is:")
        subprocess.call('date')

        # Uncomment below for testing while on network.
        # This "holds" the GPS time for 5 seconds. 
        # If on a network the time will be set by the network, the GPS will set the time 5 seconds, but 5 seconds slow, then then when the network is
        # restarted, the time will be proplerly set. 
        #time.sleep(5.0)

        print ("Setting time via GPS.")
        syslog.syslog("Setting time via GPS") 
        command = ['sudo', 'date', '-s', date_time]
        subprocess.call(command)
        
        print("The sysdate after setting with GPS is:")
        subprocess.call('date')

        break

   i += 1

print ("restarting network time servivce")
command = ['sudo', 'systemctl', 'start', 'systemd-timesyncd.service']
subprocess.call(command)
subprocess.call('date')

##### End of setting sysdate #####
