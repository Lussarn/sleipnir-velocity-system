#!/bin/env python

from SocketServer import ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import SimpleHTTPServer
import urlparse
import thread
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
   taking_pictures = False
   last_picture_timestamp = 0
   fetching_pictures = False
   ready = True

   # Frames key, timestamps value
   cameras_data = None
   timestamp_file = {"cam1" : None, "cam2" : None}

   debug = False

   camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}
   online = {"cam1": False, "cam2": False}


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
   pass

if sys.argv[1:]:
   port = int(sys.argv[1])
else:
   port = 8000

if sys.argv[2:]:
   os.chdir(sys.argv[2])

class MySimpleHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
   def log_message(self, format, *args):
      pass

class MyRequestHandler(MySimpleHTTPRequestHandler):

   def mkdir(self, cam):
      global ServerData
      flight_dir = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number))
      if not os.path.exists(flight_dir):
         os.mkdir(flight_dir);

      cam_dir = os.path.join(flight_dir, cam)
      if not os.path.exists(cam_dir):
         os.mkdir(cam_dir);


   def saveFrame(self, cam, frame, data, timestamp):
      global ServerData
      cam_dir = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number), str(cam))

      picture_directory = os.path.join(cam_dir, str((frame / 100) *100).zfill(6))
      if not os.path.exists(picture_directory):
         os.mkdir(picture_directory);

      picture_filename = os.path.join(picture_directory, "image" + str(frame).zfill(9) + ".jpg")
      file = open(picture_filename, "w")
      file.write(data)
      file.close()


   def do_GET(self):

      # Parse query data & params to find out what was passed
      parsedParams = urlparse.urlparse(self.path)
      queryParsed = urlparse.parse_qs(parsedParams.query)

      print parsedParams.path
      print queryParsed["t"]

      self.send_response(200)
      self.send_header('Content-Type', 'application/xm')
      self.end_headers()

      self.wfile.write("<?xml version='1.0'?>");
      self.wfile.write("<sample>Some XML</sample>");
      self.wfile.close();

   def do_POST(self):
      global ServerData

      ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
      if ctype == 'multipart/form-data':
         print self.rfile
         postvars = cgi.parse_multipart(self.rfile, pdict)
      elif ctype == 'application/x-www-form-urlencoded':
         length = int(self.headers.getheader('content-length'))
         postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
      else:
         postvars = {}

      action = postvars["action"][0]

      if (action == "startcamera"):
         id = postvars["id"][0]
         if id == "cam1" or id == "cam2":
            ServerData.camera_last_transmission_timestamp[id] = time.time()
            ServerData.online[id] = True

#         print "Camera " + id + " asking to start"
         if (ServerData.taking_pictures):
            self.send200("OK-START")
         else:
            self.send200("OK-STOP")
         pass

      if (action == "uploadframe"):
         if not ServerData.fetching_pictures and not ServerData.taking_pictures:
            self.send200("OK-STOP")
            return

         id = postvars["id"][0]
         if id == "cam1" or id == "cam2":
            ServerData.camera_last_transmission_timestamp[id] = time.time()
            ServerData.online[id] = True


         imageNum = int(postvars["framenumber"][0])
         timestamp = int(postvars["timestamp"][0])
         ServerData.last_picture_timestamp = time.time()
         ServerData.fetching_pictures = True

         # First frame create dir and open timestamp file
         if (imageNum == 1):
            self.mkdir(id)
            filename_timestamp = os.path.join(ServerData.cameras_directory_base, str(ServerData.flight_number), id, "timestamps.txt")
            ServerData.timestamp_file[id] = open(filename_timestamp, "w")

         if ServerData.debug:
            print "uploadpictures", id, imageNum, timestamp;
         data = base64.b64decode(postvars["data"][0])
         self.saveFrame(id, imageNum, data, timestamp)
         ServerData.timestamp_file[id].write(str(imageNum) + " " + str(timestamp) + "\n")
         ServerData.cameras_data.add_frame(id, imageNum, timestamp)
         
         if (ServerData.taking_pictures):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

   def send200(self, msg):
      self.send_response(200)
      self.send_header('Content-Type', 'text/plain')
      self.end_headers()

      self.wfile.write(msg);
      self.wfile.close();      

def __startHTTP(threadName, delay):
   server = ThreadingSimpleServer(('', port), MyRequestHandler)
   while True:
      sys.stdout.flush()
      server.handle_request()

def is_shooting():
   global ServerData
   return ServerData.fetching_pictures

def start_shooting(cameras_data, flight_number):
   global ServerData
   if not ServerData.ready:
      return False

   ServerData.flight_directory = os.path.join(ServerData.cameras_directory_base, str(flight_number))
   try:
      shutil.rmtree(ServerData.flight_directory)
   except:
      pass

   ServerData.cameras_data = cameras_data
   ServerData.ready = False
   ServerData.taking_pictures = True
   return True

def stop_shooting():
   global ServerData
   ServerData.taking_pictures = False

def is_ready():
   global ServerData
   if not ServerData.online["cam1"]:
      return False
   if not ServerData.online["cam2"]:
      return False
   return ServerData.ready

def is_online(cam):
   global ServerData
   return ServerData.online[cam]

def get_last_image(cam):
   global ServerData
   return ServerData.cameras_data.get_last_frame(cam)

def get_start_timestamp():
   global ServerData
   return ServerData.cameras_data.get_start_timestamp()

def get_time_from_image(cam, frame_number):
   global ServerData
   return self.cameras_data.get_timestamp_from_Frame(cam, frame_number)


def __run_camera(threadName, delay):
   global ServerData
   while True:
      if time.time() - ServerData.last_picture_timestamp > 5:
         ServerData.fetching_pictures = False
         ServerData.ready = True
         # Close timestamp files
         if (ServerData.timestamp_file["cam1"]):
            ServerData.timestamp_file["cam1"].close()
            ServerData.timestamp_file["cam1"] = None
         if (ServerData.timestamp_file["cam2"]):
            ServerData.timestamp_file["cam2"].close()
            ServerData.timestamp_file["cam2"] = None

      if time.time() - ServerData.camera_last_transmission_timestamp["cam1"] > 5:
         ServerData.online["cam1"] = False
      if time.time() - ServerData.camera_last_transmission_timestamp["cam2"] > 5:
         ServerData.online["cam2"] = False
      time.sleep(1)

def start_server():
   global ServerData
   if ServerData.debug:
      print "Starting up camera server"
   thread.start_new_thread(__startHTTP, ("HTTP", 1))
   thread.start_new_thread(__run_camera, ("HTTP", 1))
