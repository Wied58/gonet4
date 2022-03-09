#!/usr/bin/python3

import time
start_time = time.perf_counter()

import serial
import subprocess
import socket
import os
import sys
import shutil
from time import gmtime, strftime
from PIL import Image, ImageDraw, ImageFont, ExifTags
import glob
import re
from collections import deque
from datetime import datetime
import math
open('/home/pi/Tools/Camera/Search GPS', 'a').close()
sys.path.insert(0, '/home/pi/Tools/FetchGPS')


os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/FetchGPS) &")

start_acquire_gps_time = time.perf_counter()
import FetchGPS
open('/home/pi/Tools/Camera/Done_for_GPS', 'a').close()
end_acquire_gps_time = time.perf_counter()
gps_acquire_time = end_acquire_gps_time - start_acquire_gps_time
print(f"gps_acquire_time = {gps_acquire_time}")


os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Param) &")

from picamera import PiCamera
PiCamera.CAPTURE_TIMEOUT = 600
from time import sleep
from fractions import Fraction


### Start of hard coded image parameters 

# shutter speed (exposure time) in microseconds
shutter_speed = 6000000


# Number of images
number_of_images = 5

# Sensitivity (ISO)
ISO = 800

#Dynamic Range Compression (DRC) options :off,low,med,high
drc = 'off'

#White Balance: off,auto,sun,cloud,shade,tungsten,fluorescent,incandescent,flash,horizon
awb = 'off'

# Manually set white balance gains
white_balance_gains = (3.35, 1.59)

#Brightness
br = 50


### End of hard coded image parameters

######## Start of parameter file read ###########
# If a an argument is given to gonet4.py, that file will be read ignoring any lines that begin with # or are blank. 
# The file will be read to accept overrides of the number of images, shutter speed, and ISO settings
ifname = "default"

if  len(sys.argv) >1:

   # Here is the important part! It takes that argument parameter and assigns to a variable name, or the file we will open
   ifname = sys.argv[1]
   
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
   
   
   #       Now that we got rid of the commeted and empty lines, broke the pieces of the lines into clean pieces 
   #       we can start parsing the information into parameters to feed the camera.
   
   
   
          if stripped_spline[0] == 'number_of_images':
              number_of_images = int(stripped_spline[1])
   
          elif stripped_spline[0] == 'shutter_speed':
              shutter_speed = int(stripped_spline[1])
   
          elif stripped_spline[0] == 'ISO':
              ISO = int(stripped_spline[1])

######## End of parameter file read ###########

os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/CreateDirs) &")

tag_ss = str(round(shutter_speed/1000000, 2))

#run_start_time = time.perf_counter()

#249_220226_192746_1645903666.jpg
log_start_of_run_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
start_of_run_time = strftime("%H%M%S", gmtime())
print(f"Start_of_run_time = {log_start_of_run_time}")


version_dir = os.listdir("/home/pi/Tools/Version")
if len(version_dir) == 0: 
   version = 'UNK'
   #os.system('touch {}'.format("/home/pi/Tools/Version/UNK"))
else:
   version  = ''.join(glob.glob(os.path.join('/home/pi/Tools/Version', '*'))).split("/")[5]


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
zero_length = []
for filename in os.listdir(scratch_dir):
   if os.path.getsize(scratch_dir + filename) == 0:
     print("Deleting zero length file " + scratch_dir +  filename)
     zero_length.append(filename)
     os.remove(scratch_dir + filename)


# move any reaming jpg files to image dir
unprocessed = []
for filename in os.listdir(scratch_dir):
    if filename.endswith(".jpg"):
      unprocessed.append(filename)
      print("Moving " + scratch_dir +  filename + " to " + image_dir + filename)
      os.rename(scratch_dir + filename, image_dir + filename)






###############################
##### Start of functions  #####
###############################

def disk_stat(path):
    disk = os.statvfs(path)
    #percent = (disk.f_blocks - disk.f_bfree) * 100 / (disk.f_blocks -disk.f_bfree + disk.f_bavail) + 1
    percent = (disk.f_bavail * 100.0) / disk.f_blocks
    return percent

def convert_gps_lat_to_exif_lat(latitude):
     latitude = abs(latitude)
     mnt,sec = divmod(latitude*3600,60)
     deg,mnt = divmod(mnt,60)

     deg = int(round(deg,0))
     mnt = int(round(mnt,0))
     sec = int(round(sec,0))

     #print (f"lat_deg: {deg}, lat_min: {mnt}, lat_sec: {sec}")
     return (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")
     #print (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")


def convert_gps_long_to_exif_long(longitude):
     longitude = abs(longitude)
     mnt,sec = divmod(longitude*3600,60)
     deg,mnt = divmod(mnt,60)

     deg = int(round(deg,0))
     mnt = int(round(mnt,0))
     sec = int(round(sec,0))

     #print (f"long_deg: {deg}, long_min: {mnt}, long_sec: {sec}")
     return (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")
     #print (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")


# West, South are negative

def get_exif_lat_dir(latitude):
    if latitude >= 0:
       return "N"
    elif latitude < 0:
       return "S"


def get_exif_long_dir(longitude):
    if longitude > 0:
       return "E"
    elif longitude <= 0:
       return "W"
#################################
##### Start of main program #####
#################################

if (disk_stat('/')) < 10:
  print("exitng due to full disk")
  os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Disk_Full; crontab -r) &")
  exit()

camera_parameters = (f"version: {version}, config: {ifname}, ISO: {ISO}, speed: {shutter_speed}, images: {number_of_images}, free disk space: {(round(disk_stat('/'),2))} GB") 
print(camera_parameters)



gps_mode = FetchGPS.GPSMode
latitude = FetchGPS.GPSLat
longitude = FetchGPS.GPSLong
altitude = FetchGPS.GPSAlt

gps_data = (f"gps_mode: {FetchGPS.GPSMode}, lat: {FetchGPS.GPSLat}, long: {FetchGPS.GPSLong}, alt: {FetchGPS.GPSAlt}")
print(gps_data)

exif_latitude = convert_gps_lat_to_exif_lat(latitude)
exif_longitude = convert_gps_long_to_exif_long(longitude)
exif_gps_data =(f"exif_latitude: {exif_latitude}, exif_longitude: {exif_longitude}")
print(exif_gps_data)

##### Imaging begins here! #####


#Create image of a rectangle for text background
img = Image.new('RGB', (3040, 60), color=(0,0,0))
     
     
# place text on image, rotate and save as foreground.jpeg
     
font = ImageFont.truetype("/home/pi/Tools/Camera/dejavu/DejaVuSans-Bold.ttf",40)
d = ImageDraw.Draw(img)


# White Text
image_gps_fix = (f"{str(abs(latitude))} {get_exif_lat_dir(latitude)} {str(abs(longitude))} {get_exif_long_dir(longitude)} {altitude} M")
d.text((20,10), "Adler / Far Horizons  " + socket.gethostname() + " " + version + " Exp: " + tag_ss + "s"\
+ " ISO: " + str(ISO) + " " + strftime("%y%m%d %H:%M:%S", gmtime()) + " UTC " + image_gps_fix , font=font, fill=(255,255,255))

img.rotate(90,expand = True).save(scratch_dir + 'foreground.jpeg', 'JPEG')

     
# take a picture with pi cam!





########### Start of picamera ##############

os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Imaging) &")

start_imaging = time.perf_counter()

camera = PiCamera(sensor_mode=3)
sleep(1)
# Set a framerate of 1/6fps, then set shutter
# speed to 6s and ISO to 800
camera.framerate_range = (Fraction(1,100), Fraction(1,2)) 
camera.shutter_speed = shutter_speed
camera.iso = ISO
camera.drc_strength=drc
camera.awb_gains = white_balance_gains
camera.brightness = br
camera.still_stats = True
camera.resolution = (4056, 3040)


camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
camera.exif_tags['GPS.GPSLongitudeRef'] = get_exif_long_dir(longitude)
camera.exif_tags['GPS.GPSLatitude'] = exif_latitude 
camera.exif_tags['GPS.GPSLatitudeRef'] = get_exif_lat_dir(latitude)
camera.exif_tags['GPS.GPSAltitude'] =  str(altitude)

camera.exif_tags['IFD0.Software'] = socket.gethostname() + ' ' + version + ' WB: ' + str(white_balance_gains)

adler_exif_tags = (f"\
Hostname: {socket.gethostname()}, \
Version: {version}, \
WB: {str(white_balance_gains)}, \
Lat: {latitude}, \
Long: {longitude}, \
Alt: {altitude}\
")

camera.exif_tags['IFD0.Artist'] = adler_exif_tags 


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

end_imaging = time.perf_counter()
imaging_time = end_imaging - start_imaging
print(f"imaging_time = {imaging_time}")

######### End of picamera ###########

os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Post) &")

start_post = time.perf_counter()

photo_count = 0 
#post processing
filenames = []
#for filename in os.listdir("/home/pi/gonet3/scratch/"):
for filename in os.listdir(scratch_dir):
   if filename.endswith(".jpg"):
     sfilename = filename.split("_")
     print (scratch_dir + filename)
     filenames.append(filename)
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
print(f"filenames: {filenames}")
print(f"filenames_len: {len(filenames)}")

end_post = time.perf_counter()
post_time = end_post - start_post
print(f"post_time = {post_time}")

##### End of filename in directory for
print (f"photo_count: {photo_count}")


finish_time = time.perf_counter()
total_run_time = str(finish_time - start_time)

print(f"total_run_time: {total_run_time}, gps_acquire_time: {gps_acquire_time}, imaging_time: {imaging_time}, post_time: {post_time}")
print()

with open('/home/pi/Tools/Camera/gonet.log', 'a') as fout:
    fout.write(f"Start_of_run_time = {log_start_of_run_time}\n")
    fout.write(f"total_run_time: {total_run_time}, gps_acquire_time: {gps_acquire_time}, imaging_time: {imaging_time}, post_time: {post_time}, ")
    fout.write(f"{log_start_of_run_time} {camera_parameters}, ")
    fout.write(f"{log_start_of_run_time} {gps_data}\n")
    fout.write(f"{exif_gps_data}\n")
    for x in range(0, len(filenames)):
         fout.write(f"processed_file: {filenames[x]}\n")

    if len(zero_length) > 0:
        for x in range(0, len(zero_length)):
            fout.write(f"removing_zero_length_file: {zero_length[x]}\n")

    if len(unprocessed) > 0:
        for x in range(0, len(unprocessed)):
            fout.write(f"moving_unprocessed_file: {unprocessed[x]}\n")
        fout.write(f"\n")
    fout.write(f"\n")

with open('/home/pi/Tools/Camera/gonet.log') as foo:
    if len(foo.readlines()) > 6000:
 
         with open('/home/pi/Tools/Camera/gonet.log') as fin, open('/home/pi/Tools/Camera/temp_gonet.log', 'w') as fout:
             fout.writelines(deque(fin, 5000))
         os.remove("/home/pi/Tools/Camera/gonet.log")
         os.rename("/home/pi/Tools/Camera/temp_gonet.log","/home/pi/Tools/Camera/gonet.log")


os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Ready) &")
