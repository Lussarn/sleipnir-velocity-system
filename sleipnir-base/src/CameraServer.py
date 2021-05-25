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

from Frame import Frame
from database.DB import DB
import database.frame_dao as frame_dao

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class ServerData:
   db = None
   flight_number = 1
   request_pictures_from_camera = False
   last_picture_timestamp = 0

   # Frames key, timestamps value
   cameras_data = None
   camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}

   # performance statistics and logs
   stat_number_of_requests = 0
   stat_accumulated_time = 0
   last_log_message_cam_asking_to_start = {'cam1': 0, 'cam2': 0}


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
   """Handle requests in a separate thread."""

class SleipnirRequestHandler(http.server.SimpleHTTPRequestHandler):
   def log_message(self, format, *args):
      pass

   def do_POST(self):
      global ServerData
      start = time.time()

      ctype, pdict = cgi.parse_header(self.headers['content-type'])
      if ctype == 'multipart/form-data':
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
            logger.info("Camera " + id + " is online and asking to start")
            ServerData.last_log_message_cam_asking_to_start[id] = time.time()

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-START")
         else:
            self.send200("OK-STOP")
         pass

      if (action == "uploadframe"):
         cam = postvars[b"id"][0].decode('utf-8')
         if cam != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera id: " + cam)
            return

         ServerData.camera_last_transmission_timestamp[cam] = time.time()

         imageNum = int(postvars[b"framenumber"][0].decode('utf-8'))
         timestamp = int(postvars[b"timestamp"][0].decode('utf-8'))
         ServerData.last_picture_timestamp = time.time()

         image = base64.b64decode(postvars[b"data"][0].decode('ASCII'))

         frame = Frame(
            ServerData.flight_number,
            1 if cam == 'cam1' else 2,
            imageNum,
            timestamp,
            image
         )
         frame_dao.store(ServerData.db, frame)

         ServerData.cameras_data.add_frame(cam, imageNum, timestamp)

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

      # statistics logging
      ServerData.stat_accumulated_time += (time.time() - start)
      ServerData.stat_number_of_requests += 1
      if ServerData.stat_number_of_requests % 1000 == 0:
         logger.info("Time to POST: " + str(int(ServerData.stat_accumulated_time / ServerData.stat_number_of_requests * 1000000)/1000) + "ms")
         ServerData.stat_accumulated_time = 0
         ServerData.stat_number_of_requests = 0

   def send200(self, msg):
      self.send_response(200)
      self.send_header('Content-Type', 'text/plain')
      self.end_headers()
      self.wfile.write(msg.encode('ASCII'))

def __startHTTP(threadName, delay):
   server = ThreadingSimpleServer(('', 8000), SleipnirRequestHandler)
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
      logger.error("Unable to start shooting because camera is not online")
      return False

   try:
      start = time.time()
      logger.info("Deleting old frames and announcements...")
      frame_dao.delete_flight(ServerData.db, flight_number)
      logger.info("Time to remove pictures: " + format(time.time() - start, ".3f") + "s")
   except Exception as e:
      logger.error(str(e))
      return

   ServerData.cameras_data = cameras_data
   ServerData.request_pictures_from_camera = True
   return True

def stop_shooting():
   logger.info("Request to stop shooting")
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
   return ServerData.cameras_data.get_timestamp_from_Frame(cam, frame_number)

def start_server(db: DB):
   global ServerData
   ServerData.db = db
   logger.info("Starting camera server")
   _thread.start_new_thread(__startHTTP, ("HTTP", 0.001))
