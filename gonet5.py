#i!/usr/bin/python3



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
from datetime import datetime
import math
#from pysolar.solar import * 
#import pytz
import fetch_gps


from picamera import PiCamera
PiCamera.CAPTURE_TIMEOUT = 600
#print(PiCamera.CAPTURE_TIMEOUT)
from time import sleep
from fractions import Fraction

#import set_system_time_from_gps

### Start of hard coded image parameters 

# shutter speed (exposure time) in microseconds
#raspistill_ss = 10000 
#raspistill_ss = 6000000 
#raspistill_ss = 30000000 
shutter_speed = 6000000

#tag_raspistill_ss = str(round(raspistill_ss/1000000, 2))
#tag_raspistill_ss = str(round(shutter_speed/1000000, 2))

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
ifname = "default"

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



tag_ss = str(round(shutter_speed/1000000, 2))

run_start_time = time.time()
print ("run_start_time = " + str(run_start_time))


logfile = open("/home/pi/Tools/Camera/gonet.log","a+")
logfile.write("run_start_time = " + str(run_start_time) + "\n")
#now = datetime.now()
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

def convert_gps_lat_to_exif_lat(latitude):
     latitude = abs(latitude)
     mnt,sec = divmod(latitude*3600,60)
     deg,mnt = divmod(mnt,60)

     deg = int(round(deg,0))
     mnt = int(round(mnt,0))
     sec = int(round(sec,0))

     print (f"lat_deg: {deg}, lat_min: {mnt}, lat_sec: {sec}")
     return (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")
     print (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")


def convert_gps_long_to_exif_long(longitude):
     longitude = abs(longitude)
     mnt,sec = divmod(longitude*3600,60)
     deg,mnt = divmod(mnt,60)

     deg = int(round(deg,0))
     mnt = int(round(mnt,0))
     sec = int(round(sec,0))

     print (f"long_deg: {deg}, long_min: {mnt}, long_sec: {sec}")
     return (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")
     print (f"{str(deg)}/1,{str(mnt)}/1,{str(sec)}/1")


# West, South are negative

def get_exif_lat_dir(latitude):
    if latitude > 0:
       return "N"
    elif latitude < 0:
       return "S"


def get_exif_long_dir(longitude):
    if longitude > 0:
       return "E"
    elif longitude < 0:
       return "W"
#################################
##### Start of main program #####
#################################

print("free disk space = " + str(round(disk_stat('/'),2)) + "%")
if (disk_stat('/')) < 10:
  print("exitng due to full disk")
  os.system("(rm -rf /home/pi/Tools/Status/*; touch /home/pi/Tools/Status/Disk_Full; crontab -r) &")
  exit()


latitude = fetch_gps.GPSLat
longitude = fetch_gps.GPSLong

print (f"lat: {fetch_gps.GPSLat}")
print (f"long: {fetch_gps.GPSLong}")
print()


exif_latitude = convert_gps_lat_to_exif_lat(latitude)
print(f"exif_latitude = {exif_latitude}")
exif_longitude = convert_gps_long_to_exif_long(longitude)
print(f"exif_longitude = {exif_longitude}")

##### Imaging begins here! #####

#start_create_image_tag_time = time.time()
#gps_string_manipulation = str(start_create_image_tag_time - start_GPS_string_manipulation_time)
#print ("gps_string_manipulation = " + gps_string_manipulation)
#logfile.write("gps_string_manipulation = " + gps_string_manipulation + "\n")

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

# White Text

#d.text((20,10), "Adler / Far Horizons  " + socket.gethostname() + " " + version + " Exp: " + tag_ss + "s"\
#+ " ISO: " + str(ISO) + " " + strftime("%y%m%d %H:%M:%S", gmtime()) + " UTC " + image_gps_fix , font=font, fill=(255,255,255))

d.text((20,10), "The tag needs work   "  , font=font, fill=(255,255,255))
img.rotate(90,expand = True).save(scratch_dir + 'foreground.jpeg', 'JPEG')

     
# take a picture with pi cam!


#start_imaging_time = time.time()
#create_image_tag = str(start_imaging_time - start_create_image_tag_time)
#print ("create_image_tag = " + create_image_tag)
#logfile.write("create_image_tag = " + create_image_tag + "\n")




########### Start of picamera ##############

camera = PiCamera(sensor_mode=3)
sleep(1)
# Set a framerate of 1/6fps, then set shutter
# speed to 6s and ISO to 800
#camera.framerate = Fraction(1, 6)
camera.framerate_range = (Fraction(1,100), Fraction(1,2)) 
#camera.shutter_speed = raspistill_ss
camera.shutter_speed = shutter_speed
camera.iso = ISO
camera.drc_strength=drc
#camera.awb_mode = awb
#camera.awb_gains = (3.3476,1.5936)
camera.awb_gains = white_balance_gains
camera.brightness = br
camera.still_stats = True
#camera.resolution = (2592, 1944)
camera.resolution = (4056, 3040)


camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
camera.exif_tags['GPS.GPSLongitudeRef'] = get_exif_long_dir(longitude)
camera.exif_tags['GPS.GPSLatitude'] = exif_latitude 
camera.exif_tags['GPS.GPSLatitudeRef'] = get_exif_lat_dir(latitude)
##fix me later
##camera.exif_tags['GPS.GPSAltitude'] = exif_alt

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

#start_post_processing_time = time.time()
#imaging_time = str(start_post_processing_time - start_imaging_time)
#print ("imaging_time = " + imaging_time)
#logfile.write("imaging_time = " + imaging_time + "\n")

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



#finish_time = time.time()
#post_processing_time = str(finish_time - start_post_processing_time)
#print ("post_processing_time = " + post_processing_time)
#logfile.write("post_processing_time = " + post_processing_time + "\n")



#total_run_time = str(finish_time - run_start_time)
#print ("total_time = " + total_run_time)
#logfile.write("total_time = " + total_run_time + "\n")
#
#print ("perf," + str(run_start_time) + "," + setup_time + "," + gps_aquisition + "," + gps_string_manipulation + "," + create_image_tag + "," + imaging_time + "," + post_processing_time + "," + total_run_time + "," + str(gps_flag) + "," + str(photo_count))
#print ("")
#
##logfile.write("perf," + str(run_start_time) + "," + setup_time + "," + gps_aquisition + "," + gps_string_manipulation + "," + create_image_tag + "," + imaging_time + "," + post_processing_time + "," + total_run_time + "," + str(gps_flag) + "," + str(photo_count) + "\n")
#logfile.write("perf," + now.strftime("%m/%d/%Y, %H:%M:%S") + "," + ifname + "," + imaging_time + "," + post_processing_time + "," + total_run_time + "," + str(photo_count) + "\n")
#logfile.write("\n")
#
logfile.flush()
logfile.close()
#
#with open('/home/pi/Tools/Camera/gonet.log') as fin, open('/home/pi/Tools/Camera/temp_gonet.log', 'w') as fout:
#    fout.writelines(deque(fin, 10000))
#os.remove("/home/pi/Tools/Camera/gonet.log")
#os.rename("/home/pi/Tools/Camera/temp_gonet.log","/home/pi/Tools/Camera/gonet.log")
