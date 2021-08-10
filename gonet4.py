#!/usr/bin/python3

import serial
import subprocess
import socket
import os
import sys
import shutil
import time
from time import gmtime, strftime
from PIL import Image, ImageDraw, ImageFont, ExifTags
import glob
import re
from collections import deque
import syslog
from datetime import datetime

from picamera import PiCamera
PiCamera.CAPTURE_TIMEOUT = 600
#print(PiCamera.CAPTURE_TIMEOUT)
from time import sleep
from fractions import Fraction


### Start of hard coded image parameters 

# shutter speed (exposure time) in microseconds
#raspistill_ss = 10000 
raspistill_ss = 6000000 
#raspistill_ss = 30000000 

tag_raspistill_ss = str(round(raspistill_ss/1000000, 2))

# Number of images
number_of_images = 5

# Sensitivity (ISO)
ISO = 800

#Dynamic Range Compression (DRC) options :off,low,med,high
drc = 'off'

#White Balance: off,auto,sun,cloud,shade,tungsten,fluorescent,incandescent,flash,horizon
awb = 'off'

# Manually set white balance gains
#white_balance_gains = ('3.35, 1.59')
white_balance_gains = (3.35, 1.59)

#Brightness
br = 50


### End of hard coded image parameters

######## Start of parameter file read ###########
# If a an argument is given to gonet4.py, that file will be read ignoring any lines that begin with # or are blank. 
# The file will be read to accept overrides of the number of images, shutter speed, and ISO settings

if  len(sys.argv) >1:

   # Here is the important part! It takes that argument parameter and assigns to a variable name, or the file we will open
   ifname = sys.argv[1]
   print(f"Using config file {ifname}")
   
   # open the file config.txt file
   with open(ifname) as params:
   
     #iterate (loop) through the lines of the file
     for line in params:
   
   #   if the line does not start with # and is longer than 0 after stripping leading and trailing spaces, process it.  We'll talk about strip later

       if line[0] != '#' and len(line.strip()) > 0: 
   
   #      We replace the newline \n, then split the line at the equal sign.
          spline = line.replace('\n','').split('=')
   #       print(spline)
   
   
   #      Here we iterate, or loop, across the list, strip the spaces off the ends of the list elements
          stripped_spline = [x.strip() for x in spline]
   
   #      Now we print the pieces, or elemments of the list.
   #       print(stripped_spline[0], stripped_spline[1])
   
   
   #       Now that we got rid of the commeted and empty lines, broke the pieces of the lines into clean pieces 
   #       we can start parsing the information into parameters to feed the camera.
   
   
   
          if stripped_spline[0] == 'number_of_images':
              number_of_images = int(stripped_spline[1])
              print (f"Overriding number_of_images from config file to: {number_of_images}")
   
          elif stripped_spline[0] == 'shutter_speed':
              shutter_speed = int(stripped_spline[1])
              #(shutter_speed)
              print (f"Overriding shutter_speed from config file to: {shutter_speed}")
   
          elif stripped_spline[0] == 'ISO':
              ISO = int(stripped_spline[1])
              print (f"Overriding ISO from config file to: {ISO}") 

######## End of parameter file read ###########

run_start_time = time.time()
print ("run_start_time = " + str(run_start_time))


logfile = open("/home/pi/Tools/Camera/gonet.log","a+")
logfile.write("run_start_time = " + str(run_start_time) + "\n")
now = datetime.now()
#logfile.write("run_start_time = " + now.strftime("%m/%d/%Y, %H:%M:%S") + "\n")

#print ("run_start_time = " + now.strftime("%m/%d/%Y, %H:%M:%S"))

scratch_dir = "/home/pi/Tools/Camera/scratch/"
if not os.path.exists(scratch_dir):
    os.makedirs(scratch_dir)

image_dir = "/home/pi/images/"
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

thumbs_dir = "/home/pi/_sfpg_data/thumb/"
if not os.path.exists(thumbs_dir):
    os.makedirs(thumbs_dir)

# remove  any zero length file from scratch dir

for filename in os.listdir(scratch_dir):
   if os.path.getsize(scratch_dir + filename) == 0:
     print("Deleting zero length file " + scratch_dir +  filename)
     logfile.write(("Deleting zero length file " + scratch_dir +  filename) + "\n")
     os.remove(scratch_dir + filename)


# move any reaming jpg files to image dir

for filename in os.listdir(scratch_dir):
    if filename.endswith(".jpg"):
      print("Moving " + scratch_dir +  filename + " to " + image_dir + filename)
      logfile.write(("Moving " + scratch_dir +  filename + " to " + image_dir + filename)  + "\n")
      os.rename(scratch_dir + filename, image_dir + filename)

# Here date and time is captured from GPS $GPRMC if available.
# The time service from the network is shutdown, and system time is set from GPS value.
# Then the network time service is restarted in case the device is being tested indoors
# and network is accessible and GPS is not. 
#
# This is in case the program is executed without access to netork.
# It is ran everytime the program is executed in case GPS is not valid when the GONet
# device is first turned on. 
#
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

#run_start_time = time.time()
#print ("run_start_time = " + str(run_start_time))




###############################
##### Start of functions  #####
###############################

def disk_stat(path):
    disk = os.statvfs(path)
    #percent = (disk.f_blocks - disk.f_bfree) * 100 / (disk.f_blocks -disk.f_bfree + disk.f_bavail) + 1
    percent = (disk.f_bavail * 100.0) / disk.f_blocks
    return percent

##### end of parse gga #####

def parse_gga(sdata):
     lat = sdata[2]
     lat_dir = sdata[3]
     long = sdata[4]
     long_dir = sdata[5]
     alt = sdata[9]

     return  lat + " " + lat_dir + " " + long + " " + long_dir + " " + alt + " M"

##### end of parse gga #####

def convert_to_dd(x):
  
   x=float(x)
   degrees = int(x) // 100
   minutes = (x - 100*degrees) / 60
   dd = str(round((degrees + minutes),6))
  
   return dd

##### end of convert_to_dd  #####

#def lat_long_decode(coord):
#    #Converts DDDMM.MMMMM > DD  MM' SS.SSS" 
#    x = coord.split(".")
#    head = x[0]
#    tail = x[1]
#    deg = head[0:-2]
#    min = head[-2:]
#    #sec = str((float(coord[-6:]) * 60.0))
#    sec = str((float("." + tail) * 60.0))
#
#    #return deg + "  " + min + " " + sec + " "
#    return deg + u"\u00b0 " + min + "\' " + sec + "\""
#
###### end of lat_long_decode #####



def convert_raw_gps_fix_to_image_gps_fix(raw_gps_fix):
     #4203.4338X N 08748.7831X W 215.3 M
     print("here is the raw gps fix for finding da error")
     print(raw_gps_fix)
     sraw_gps_fix = raw_gps_fix.split(" ")
     #lat = lat_long_decode(sraw_gps_fix[0])
     lat = convert_to_dd(sraw_gps_fix[0])
     lat_dir = sraw_gps_fix[1]
     #long = lat_long_decode(sraw_gps_fix[2])
     long = convert_to_dd(sraw_gps_fix[2])
     long_dir = sraw_gps_fix[3]
     alt = sraw_gps_fix[4]

     return  lat + " " + lat_dir + " " + long + " " + long_dir + " " + alt + " M"

##### end of convert_raw_gps_fix_to_image_gps_fix #####

def convert_raw_gps_fix_to_exif_lat(raw_gps_fix):
     raw_lat = (raw_gps_fix.split(" "))[0]
     deg = raw_lat[0:2]
     min = raw_lat[2:4]
     sec = str(int(float(raw_lat[4:9]) * 60.0))
     #sec = str(float(raw_lat[5:9]) * 60.0 / 10000)
     return deg + "/1," + min + "/1," + sec + "/1"
     #return deg + "/1," + min + "/1," + sec + "/1000"

##### end of convert_raw_gps_fix_to_exif_lat #####

def convert_raw_gps_fix_to_exif_lat_dir(raw_gps_fix):
    print("I'm in convert_raw_gps_fix_to_exif_lat_dir")
    return (raw_gps_fix.split(" "))[1]

##### end of convert_raw_gps_fix_to_exif_lat_dir #####


def convert_raw_gps_fix_to_exif_long(raw_gps_fix):
     raw_lat = (raw_gps_fix.split(" "))[2]
     deg = raw_lat[0:3]
     min = raw_lat[3:5]
     sec = str(int((float(raw_lat[5:10]) * 60.0)))
     return deg + "/1," + min + "/1," + sec + "/1"
     #return deg + "/1," + min + "/1," + sec + "/1000"

##### end of convert_raw_gps_fix_to_exif_long #####


def convert_raw_gps_fix_to_exif_long_dir(raw_gps_fix):
    return (raw_gps_fix.split(" "))[3]

##### end of convert_raw_gps_fix_to_exif_long_dir #####



def convert_raw_gps_fix_to_exif_alt(raw_gps_fix):
    return (raw_gps_fix.split(" "))[4]

##### end of convert_raw_gps_fix_to_exif_alt #####

def nmea_cksum(data):
     
     # http://doschman.blogspot.com/2013/01/calculating-nmea-sentence-checksums.html
     # Thiss is a string, will need to convert it to hex for
     # proper comparsion below
     

     ck_sum = data[len(data) - 4:] 

     # String slicing: Grabs all the characters
     # between '$' and '*' and nukes any lingering
     # newline or CRLF
     chksumdata = re.sub("(\n|\r\n)","", data[data.find("$")+1:data.find("*")])
     
     # Initializing our first XOR value
     csum = 0
     
     # For each char in chksumdata, XOR against the previous
     # XOR'd char.  The final XOR of the last char will be our
     # checksum to verify against the checksum we sliced off
     # the NMEA sentence
     
     for c in chksumdata:
        # XOR'ing value of csum against the next char in line
        # and storing the new XOR value in csum
        csum ^= ord(c)
     
     # Do we have a validated sentence?
     if hex(csum) == hex(int(ck_sum, 16)):
        return True
     
     return False

##### end of convert_raw_gps_fix_to_exif_long #####

#################################
##### Start of main program #####
#################################

print("free disk space = " + str(round(disk_stat('/'),2)) + "%")
if (disk_stat('/')) < 10:
  print("exitng due to full disk")
  os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Disk_Full; crontab -r) &")
  exit()


start_looking_for_GPS_time  = time.time()
setup_time = str((start_looking_for_GPS_time - run_start_time))

print ("setup_time = " + setup_time)
logfile.write("setup_time = " + setup_time + "\n")

os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Imaging...) &")

print  ("Looking for GPS Data")
logfile.write("Looking for GPS Data" + "\n")

#while True:
gps_time_out = 0
while  gps_time_out < 35:
   time.sleep(1.0)
   data = ser.readline().decode('utf_8') 
   #data = ser.read_until()
   sdata = data.split(',')

   if sdata[0] == "$GPGGA" and sdata[6] in ("1","2"):
          if nmea_cksum(data):

              print ("GPS Checksum Passed")
              logfile.write("GPS Checksum Passed" + "\n")

              for fl in glob.glob("/home/pi/Tools/Camera/GPS/GPGGA*"):
                    os.remove(fl)
    
              filename = "/home/pi/Tools/Camera/GPS/" + data[1:]
              mode = 0o644
              os.mknod(filename, mode)
    
              print (filename,)
              logfile.write(filename)
 
              raw_gps_fix  = parse_gga(sdata)
              gps_flag = 2
              break 
          else:
              print ("GPS Checksum Failed")
    # end of if sdata[0] == "$GPGGA" and sdata[6] in ("1","2")

   elif sdata[0] == "$GPGGA" and sdata[6] == "0":
         if nmea_cksum(data):

             print ("GPS Checksum Passed")
             logfile.write("GPS Checksum Passed\n")

             for fl in glob.glob("/home/pi/Tools/Camera/GPS/GPGGA*"):
                   os.remove(fl)
    
             filename = "/home/pi/Tools/Camera/GPS/" + data[1:]
             mode = 0o644
             os.mknod(filename, mode)
    
             print (filename,)
             logfile.write(filename)
 
             print (gps_time_out)
             logfile.write(str(gps_time_out) + "\n")
       
             if  gps_time_out>= 25:
                  # We are receiving data from the GPS, not can't get a fix.
                  # Giving up, we must be in the basement.
                  gps_flag = 1
                  break
         else:
             print ("GPS Checksum Failed")
             logfile.write("GPS Checksum Failed" + "\n")
                 
   gps_flag = 0
   gps_time_out += 1

##### end of gps_time_out while #####

ser.close()

print ("gps_flag = " + str(gps_flag))
logfile.write("gps_flag = " + str(gps_flag) + "\n")

##### done with gps #####



##### manuipilate gps strings to make them useful #####


start_GPS_string_manipulation_time = time.time()
gps_aquisition = str(start_GPS_string_manipulation_time - start_looking_for_GPS_time)
print ("gps_aquisition = " + gps_aquisition)
logfile.write("gps_aquisition = " + gps_aquisition + "\n")

if gps_flag == 0:

   image_gps_fix = "GPS Not Available"

   print ("GPS Not Responsive, proceeding to collect images.")
   logfile.write("GPS Not Responsive, proceeding to collect images.")

   exif_lat = '00/1,00/1,00.00/1'
   exif_lat_dir = 'X'
   exif_long = '000/1,00/1,00.0000/1'
   exif_long_dir = 'X' 
   exif_alt = '0'

   for fl in glob.glob("/home/pi/Tools/Camera/GPS/GPGGA*"):
         os.remove(fl)

   filename = "/home/pi/Tools/Camera/GPS/GPGGA,ERROR" 
   mode = 0o644
   os.mknod(filename, mode)

if gps_flag == 1:

   image_gps_fix = "GPS Fix Not Available"

   print ("GPS Not Fix Available, proceeding to collect images.")
   logfile.write("GPS Not Fix Available, proceeding to collect images.")

   exif_lat = '00/1,00/1,00.00/1'
   exif_lat_dir = 'X'
   exif_long = '000/1,00/1,00.0000/1'
   exif_long_dir = 'X'
   exif_alt = '0'



if gps_flag == 2:

   image_gps_fix = convert_raw_gps_fix_to_image_gps_fix(raw_gps_fix)
   print ("Raw GPS Data = " + raw_gps_fix)
   logfile.write("Raw GPS Data = " + raw_gps_fix + "\n")
#   print ("Processed GPS Data = " + image_gps_fix)
#   logfile.write("Processed GPS Data = " + image_gps_fix + "\n")
   
   exif_lat = convert_raw_gps_fix_to_exif_lat(raw_gps_fix)
   exif_lat_dir = convert_raw_gps_fix_to_exif_lat_dir(raw_gps_fix)
   exif_long = convert_raw_gps_fix_to_exif_long(raw_gps_fix)
   exif_long_dir = convert_raw_gps_fix_to_exif_long_dir(raw_gps_fix)
   exif_alt = convert_raw_gps_fix_to_exif_alt(raw_gps_fix)

##### done with gps string manipulation #####



##### Imaging begins here! #####

start_create_image_tag_time = time.time()
gps_string_manipulation = str(start_create_image_tag_time - start_GPS_string_manipulation_time)
print ("gps_string_manipulation = " + gps_string_manipulation)
logfile.write("gps_string_manipulation = " + gps_string_manipulation + "\n")

#Create image of a rectangle for text background
#img = Image.new('RGB', (1944, 120), color=(255,255,255))
#img = Image.new('RGB', (1944, 120), color=(0,0,0))
img = Image.new('RGB', (3040, 60), color=(0,0,0))
     
     
# place text on image, rotate and save as foreground.jpeg
     
font = ImageFont.truetype("/home/pi/Tools/Camera/dejavu/DejaVuSans-Bold.ttf",40)
d = ImageDraw.Draw(img)



version_dir = os.listdir("/home/pi/Tools/Version")
#print(version_dir)
#print (len(version_dir))
if len(version_dir) == 0: 
   print("Empty directory using UNK")
   version = 'UNK'
   #os.system('touch {}'.format("/home/pi/Tools/Version/UNK"))
else:
   version  = ''.join(glob.glob(os.path.join('/home/pi/Tools/Version', '*'))).split("/")[5]
print (version)

## Old gonet3.py tag
## White Text
##d.text((20,10), "Adler / Far Horizons  " + socket.gethostname() + " " + version + " Exp: " + tag_raspistill_ss + " S"\
#+ " ISO: " + str(ISO) + " WB: " + str(white_balance_gains), font=font, fill=(255,255,255))
## Next Line 
#d.text((20,70), strftime("%y%m%d %H:%M:%S", gmtime()) + " UTC " + image_gps_fix , font=font, fill=(255,255,255))
#img.rotate(90,expand = True).save(scratch_dir + 'foreground.jpeg', 'JPEG')
     
# White Text
d.text((20,10), "Adler / Far Horizons  " + socket.gethostname() + " " + version + " Exp: " + tag_raspistill_ss + " S"\
+ " ISO: " + str(ISO) + " " + strftime("%y%m%d %H:%M:%S", gmtime()) + " UTC " + image_gps_fix , font=font, fill=(255,255,255))
img.rotate(90,expand = True).save(scratch_dir + 'foreground.jpeg', 'JPEG')

     
# take a picture with pi cam!


start_imaging_time = time.time()
create_image_tag = str(start_imaging_time - start_create_image_tag_time)
print ("create_image_tag = " + create_image_tag)
logfile.write("create_image_tag = " + create_image_tag + "\n")

########### start of raspistill  ##############

#image_file_name = socket.gethostname()[-3:] + "_" + (strftime("%y%m%d_%H%M%S", gmtime())) + "_%03d"
image_file_name = socket.gethostname()[-3:] + "_" + (strftime("%y%m%d_%H%M%S", gmtime())) + "_%d"
print ("image_file_name = " + image_file_name)
logfile.write("image_file_name = " + image_file_name + "\n")

##command = ['/usr/bin/raspistill', '-v',
#                         '-t', str(raspistill_t),
#                         '-ss', str(raspistill_ss),
#                         '-tl', str(raspistill_tl),
#                         '-ISO', str(ISO),
#                         '-drc', str(drc),
#                         '-awb', awb,
#                         #'-awbg', '1.03125, 1.8086',
#                         '-awbg', white_balance_gains,
#                         '-br', str(br),
#                         '-r',
#                         '-ts',
#                         #'--timeout', '1',
#                         '-st',
#                         #'-set',
#                         '-x', 'GPS.GPSLongitude=' + exif_long, 
#                         '-x', 'GPS.GPSLongitudeRef=' + exif_long_dir,
#                         '-x', 'GPS.GPSLatitude=' + exif_lat,
#                         '-x', 'GPS.GPSLatitudeRef=' + exif_lat_dir,
#                         '-x', 'GPS.GPSAltitude=' + exif_alt,
#                         #'-x', 'IFD0.Artist=GONet ' + white_balance_gains,
#                         '-x', 'IFD0.Software=' + socket.gethostname() + ' ' + version + ' WB: ' + white_balance_gains, 
#                         #'-x', 'IDF0.HostComputer= ' + socket.gethostname(),
#                         '-o', scratch_dir + image_file_name + '.jpg']
#subprocess.call(command)

########## end of raspistill  ##############



########### Start of picamera ##############

camera = PiCamera(sensor_mode=3)
sleep(1)
# Set a framerate of 1/6fps, then set shutter
# speed to 6s and ISO to 800
#camera.framerate = Fraction(1, 6)
camera.framerate_range = (Fraction(1,100), Fraction(1,2)) 
camera.shutter_speed = raspistill_ss
camera.iso = ISO
camera.drc_strength=drc
#camera.awb_mode = awb
#camera.awb_gains = (3.3476,1.5936)
camera.awb_gains = white_balance_gains
camera.brightness = br
camera.still_stats = True
#camera.resolution = (2592, 1944)
camera.resolution = (4056, 3040)


camera.exif_tags['GPS.GPSLongitude'] = exif_long
camera.exif_tags['GPS.GPSLongitudeRef'] = exif_long_dir
camera.exif_tags['GPS.GPSLatitude'] = exif_lat
camera.exif_tags['GPS.GPSLatitudeRef'] = exif_lat_dir
camera.exif_tags['GPS.GPSAltitude'] = exif_alt

camera.exif_tags['IFD0.Software'] = socket.gethostname() + ' ' + version + ' WB: ' + str(white_balance_gains)

start_of_run_time = strftime("%H%M%S", gmtime())
print(f"Start of run time = {start_of_run_time}")

#for x in range(5):
for x in range(number_of_images):
   #filename = socket.gethostname()[-3:] + "_" + (strftime("%y%m%d_%H%M%S_%s", gmtime()))  + ".jpg"
   filename = socket.gethostname()[-3:] + "_" + (strftime("%y%m%d_", gmtime()))  + start_of_run_time + (strftime("_%s", gmtime())) + ".jpg"
   print(scratch_dir + filename)
   camera.capture(scratch_dir + filename, bayer=True)
   #camera.capture("J_" + filename)

#print("camera parameters")
#print(camera.resolution)
#print(camera.sensor_mode)
#print(camera.awb_gains)

print("Closing Camera")
camera.close()

######### End of picamera ###########

start_post_processing_time = time.time()
imaging_time = str(start_post_processing_time - start_imaging_time)
print ("imaging_time = " + imaging_time)
logfile.write("imaging_time = " + imaging_time + "\n")

photo_count = 0 
#post processing
#for filename in os.listdir("/home/pi/gonet3/scratch/"):
for filename in os.listdir(scratch_dir):
   if filename.endswith(".jpg"):
     sfilename = filename.split("_")
     print (scratch_dir + filename)
     logfile.write(scratch_dir + filename + "\n")
     #logfile.write(scratch_dir + filename + "\n")

     # open the the image from pi cam
     background = Image.open(scratch_dir + filename).convert("RGB")

     # save its exif -  does not include raw (bayer) data
     exif = background.info['exif']

     #print(exif)

     # open foreground.jpg and paste it to pi cam image
     foreground = Image.open(scratch_dir + "foreground.jpeg")
     background.paste(foreground, (0, 0)) #, foreground)

     #save the new composite image with pi cam photo's exif
     background.save(image_dir + filename, 'JPEG',  exif=exif)

     # open the composited file for append. then tail the raw file raw data from the original to the end of composited file.
     composite_file = open(image_dir + filename, 'a') 
     #subprocess.call(['tail', '-c', '10237440', scratch_dir + filename], stdout=composite_file)
     # from: https://www.raspberrypi.org/forums/viewtopic.php?t=273500
     subprocess.call(['tail', '-c', '18711040', scratch_dir + filename], stdout=composite_file)


     # create thumnail here?
     MAX_SIZE = (160, 120) 
     background.thumbnail(MAX_SIZE)  
     background.save(thumbs_dir + filename, 'JPEG')

     # clean up the scratch directory
     os.remove(scratch_dir + filename)
     photo_count += 1
   ##### End of .jpg if
##### End of filename in directory for
print ("photo_count = " + str(photo_count))
logfile.write("photo_count = " + str(photo_count) + "\n")

os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Ready) &")



finish_time = time.time()
post_processing_time = str(finish_time - start_post_processing_time)
print ("post_processing_time = " + post_processing_time)
logfile.write("post_processing_time = " + post_processing_time + "\n")



total_run_time = str(finish_time - run_start_time)
print ("total_time = " + total_run_time)
logfile.write("total_time = " + total_run_time + "\n")

print ("perf," + str(run_start_time) + "," + setup_time + "," + gps_aquisition + "," + gps_string_manipulation + "," + create_image_tag + "," + imaging_time + "," + post_processing_time + "," + total_run_time + "," + str(gps_flag) + "," + str(photo_count))
print ("")

logfile.write("perf," + str(run_start_time) + "," + setup_time + "," + gps_aquisition + "," + gps_string_manipulation + "," + create_image_tag + "," + imaging_time + "," + post_processing_time + "," + total_run_time + "," + str(gps_flag) + "," + str(photo_count) + "\n")
logfile.write("\n")

logfile.flush()
logfile.close()

with open('/home/pi/Tools/Camera/gonet.log') as fin, open('/home/pi/Tools/Camera/temp_gonet.log', 'w') as fout:
    fout.writelines(deque(fin, 10000))
os.remove("/home/pi/Tools/Camera/gonet.log")
os.rename("/home/pi/Tools/Camera/temp_gonet.log","/home/pi/Tools/Camera/gonet.log")
