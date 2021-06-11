#!/bin/env python

from urllib.parse import urlparse
import urllib
import _thread
import time
import cgi
import logging
import base64
import sys

from Frame import Frame
from database.DB import DB
import database.frame_dao as frame_dao
from function_timer import timer
import asyncio
import tornado.ioloop
import tornado.web

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger('tornado.access').disabled = True
logger = logging.getLogger(__name__)

class ServerData:
   db = None
   flight = 1
   request_pictures_from_camera = False
   last_picture_timestamp = 0

   # Frames key, timestamps value
   cameras_data = None
   camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}

   # logs
   last_log_message_cam_asking_to_start = {'cam1': 0, 'cam2': 0}

class TornadoHandler(tornado.web.RequestHandler):
   def log_message(self, format, *args):
      pass

   @timer("Http POST", logging.INFO, identifier=None, average=1000)
   def post(self):
      global ServerData

      action = self.get_argument("action", None, True)

      if (action == "startcamera"):
         id = self.get_argument("cam", None, True)
         if id != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera id: " + id)
            return

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
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera id: " + cam)
            return

         ServerData.camera_last_transmission_timestamp[cam] = time.time()

         position = int(self.get_argument("position", None, True))
         timestamp = int(self.get_argument("timestamp", None, True))
         ServerData.last_picture_timestamp = time.time()

         image = self.request.body

         frame = Frame(
            ServerData.flight,
            1 if cam == 'cam1' else 2,
            position,
            timestamp,
            image
         )
         frame_dao.store(ServerData.db, frame)

         ''' Clear the image for memory reasons '''
         frame.set_image(None)
         if not ServerData.cameras_data.add_frame(frame):
            logger.critical("Shooting stoped after failed add frame!")
            stop_shooting()

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

   def send200(self, msg):
      self.set_status(200)
      self.set_header('Content-Type', 'text/plain')
      payload = msg.encode('ASCII')
      self.write(payload)

def __startHTTP():
   asyncio.set_event_loop(asyncio.new_event_loop())
   app = tornado.web.Application([
      (r"/", TornadoHandler),
   ])
   app.listen(8000)
   tornado.ioloop.IOLoop.instance().start()

def is_shooting():
   global ServerData
   return ServerData.request_pictures_from_camera and time.time() - ServerData.last_picture_timestamp < 1

def start_shooting(cameras_data, flight):
   global ServerData
   if ServerData.request_pictures_from_camera:
      return False

   if not is_online('cam1') and not is_online('cam2'):
      logger.error("Unable to start shooting because camera is not online")
      return False

   try:
      start = time.time()
      logger.info("Deleting old frames and announcements...")
      frame_dao.delete_flight(ServerData.db, flight)
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

def start_server(db: DB):
   global ServerData
   ServerData.db = db
   logger.info("Starting camera server")
   _thread.start_new_thread(__startHTTP, ())
