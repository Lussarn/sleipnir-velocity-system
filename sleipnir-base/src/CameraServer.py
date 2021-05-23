#!/bin/env python

from socketserver import ThreadingMixIn
from http.server import SimpleHTTPRequestHandler
from http.server import HTTPServer
import http.server
from urllib.parse import urlparse
import urllib
import _thread
import time
import cgi
import logging
import base64
import sys
import os
import shutil

import CamerasData

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class ServerData:
   cameras_directory_base = ""
   flight_number = 1
   request_pictures_from_camera = False
   last_picture_timestamp = 0

   # Frames key, timestamps value
   cameras_data = None

   debug = False

   camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}

   # performance statistics and logs
   stat_number_of_requests = 0
   stat_accumulated_time = 0
   last_log_message_cam_asking_to_start = {'cam1': 0, 'cam2': 0}


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
   pass

if sys.argv[1:]:
   port = int(sys.argv[1])
else:
   port = 8000

if sys.argv[2:]:
   os.chdir(sys.argv[2])

class MySimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
   def log_message(self, format, *args):
      pass

class MyRequestHandler(MySimpleHTTPRequestHandler):

   def mkdir(self, cam):
      global ServerData
      flight_dir = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number))
      if not os.path.exists(flight_dir):
         os.mkdir(flight_dir)

      cam_dir = os.path.join(flight_dir, cam)
      if not os.path.exists(cam_dir):
         os.mkdir(cam_dir)

   def saveFrame(self, cam, frame, data, timestamp):
      global ServerData
      cam_dir = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number), str(cam))

      picture_directory = os.path.join(cam_dir, str(int(frame / 100) *100).zfill(6))
      if not os.path.exists(picture_directory):
         os.mkdir(picture_directory)

      picture_filename = os.path.join(picture_directory, "image" + str(frame).zfill(9) + ".jpg")
      file = open(picture_filename, "wb")
      file.write(data)
      file.close()

   def do_POST(self):
      global ServerData
      start = time.time()

#      ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
      ctype, pdict = cgi.parse_header(self.headers['content-type'])
      if ctype == 'multipart/form-data':
#         print (self.rfile)
         postvars = cgi.parse_multipart(self.rfile, pdict)
      elif ctype == 'application/x-www-form-urlencoded':
         length = int(self.headers['content-length'])
         postvars = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=1)
      else:
         postvars = {}

      action = postvars[b'action'][0].decode('utf-8')

      if (action == "startcamera"):
         id = postvars[b'id'][0].decode('utf-8')
         if id == "cam1" or id == "cam2":
            ServerData.camera_last_transmission_timestamp[id] = time.time()

         if (time.time() -  ServerData.last_log_message_cam_asking_to_start[id] > 10):
            print("INFO: CameraServer.do_POST() Camera " + id + " is online and asking to start")
            ServerData.last_log_message_cam_asking_to_start[id] = time.time()

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-START")
         else:
            self.send200("OK-STOP")
         pass

      if (action == "uploadframe"):

         id = postvars[b"id"][0].decode('utf-8')
         if id == "cam1" or id == "cam2":
            ServerData.camera_last_transmission_timestamp[id] = time.time()

         imageNum = int(postvars[b"framenumber"][0].decode('utf-8'))
         timestamp = int(postvars[b"timestamp"][0].decode('utf-8'))
         ServerData.last_picture_timestamp = time.time()

         filename_timestamp = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number), id, "timestamps.txt")

         # First frame create dir and open timestamp file
         if (imageNum == 1): 
            self.mkdir(id)
            
         file_timestamp = open(filename_timestamp, "a")
         file_timestamp.write(str(imageNum) + " " + str(timestamp) + "\n")
         file_timestamp.close()

         if ServerData.debug: print ("uploadpictures", id, imageNum, timestamp)

         data = base64.b64decode(postvars[b"data"][0].decode('ASCII'))
         self.saveFrame(id, imageNum, data, timestamp)

         ServerData.cameras_data.add_frame(id, imageNum, timestamp)

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

      # statistics logging
      ServerData.stat_accumulated_time += (time.time() - start)
      ServerData.stat_number_of_requests += 1
      if ServerData.stat_number_of_requests % 1000 == 0:
         print("INFO: CameraServer.do_POST() Time to POST: " + str(int(ServerData.stat_accumulated_time / ServerData.stat_number_of_requests * 1000000)/1000) + "ms")
         ServerData.stat_accumulated_time = 0
         ServerData.stat_number_of_requests = 0


   def send200(self, msg):
      self.send_response(200)
      self.send_header('Content-Type', 'text/plain')
      self.end_headers()
      self.wfile.write(msg.encode('ASCII'))

def __startHTTP(threadName, delay):
   server = ThreadingSimpleServer(('', port), MyRequestHandler)
   while True:
      sys.stdout.flush()
      server.handle_request()

def is_shooting():
   global ServerData
   return ServerData.request_pictures_from_camera and time.time() - ServerData.last_picture_timestamp < 1

def start_shooting(cameras_data, flight_number):
   global ServerData
   if ServerData.request_pictures_from_camera:
      return False

   if not is_online('cam1') and not is_online('cam2'):
      print("ERROR: CameraServer.start_shooting() Unable to start shooting because camera is not online")
      return False

   ServerData.flight_directory = os.path.join(ServerData.cameras_directory_base, str(flight_number))
   try:
      start = time.time()
      print("INFO: CameraServer.start_shooting() Removing old flight pictures in " + ServerData.flight_directory)
      shutil.rmtree(ServerData.flight_directory)
      print("INFO: CameraServer.start_shooting() Time to remove pictures: " + str((int(time.time() - start)*100)/100) + "s")
   except:
      pass

   ServerData.cameras_data = cameras_data
   ServerData.request_pictures_from_camera = True
   return True

def stop_shooting():
   global ServerData
   ServerData.request_pictures_from_camera = False

# Both cameras online and not currently requesting pictures
def is_ready_to_shoot():
   global ServerData
   if not is_online("cam1"):
      return False
   if not is_online("cam2"):
      return False
   return not ServerData.request_pictures_from_camera

# Have camera been seen for 5 seconds
def is_online(cam):
   global ServerData
   return time.time() - ServerData.camera_last_transmission_timestamp[cam] < 5

def get_next_image(cam):
   global ServerData
   return ServerData.cameras_data.get_next_frame(cam)

def get_last_image(cam):
   global ServerData
   return ServerData.cameras_data.get_last_frame(cam)

def get_start_timestamp():
   global ServerData
   return ServerData.cameras_data.get_start_timestamp()

def get_time_from_image(cam, frame_number):
   global ServerData
   return self.cameras_data.get_timestamp_from_Frame(cam, frame_number)

def start_server():
   print("INFO: CameraServer.start_server() Starting Camera Server")
   _thread.start_new_thread(__startHTTP, ("HTTP", 0.001))
