#!/bin/env python

import _thread

from urllib.parse import urlparse
import time
import logging
import asyncio
import tornado.ioloop
import tornado.web

from Frame import Frame
from database.DB import DB
import database.frame_dao as frame_dao
from function_timer import timer
from Event import Event

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger('tornado.access').disabled = True
logger = logging.getLogger(__name__)

class ServerData:
   camera_server = None # type: CameraServer

   db = None
   flight = 1
   request_pictures_from_camera = False
   last_picture_timestamp = 0

   # Frames key, timestamps value
   cameras_data = None
   camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}

   # onlide status
   camera_online_status = {"cam1": False, "cam2": False}

   # logs
   last_log_message_cam_asking_to_start = {'cam1': 0, 'cam2': 0}

class TornadoHandler(tornado.web.RequestHandler):
   def log_message(self, format, *args):
      pass

   @timer("Http POST", logging.INFO, identifier=None, average=1000)
   def post(self):
      global ServerData

      action = self.get_argument("action", None, True)

      cam = ""
      if (action == "startcamera"):
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera: " + cam)
            return

         if cam == "cam1" or cam == "cam2":
            ServerData.camera_last_transmission_timestamp[cam] = time.time()

         if (time.time() -  ServerData.last_log_message_cam_asking_to_start[cam] > 10):
            logger.info("Camera " + cam + " is online and asking to start")
            ServerData.last_log_message_cam_asking_to_start[cam] = time.time()

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
            ServerData.camera_server.stop_shooting()

         if (ServerData.request_pictures_from_camera):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

   def send200(self, msg):
      self.set_status(200)
      self.set_header('Content-Type', 'text/plain')
      payload = msg.encode('ASCII')
      self.write(payload)



class CameraServer:
   EVENT_CAMERA_ONLINE = "cameraserver.camera_online"
   EVENT_CAMERA_OFFLINE = "cameraserver.camera_offline"

   def __init__(self):
      global ServerData
      ServerData.camera_server = self


   def __startHTTP(self):
      asyncio.set_event_loop(asyncio.new_event_loop())
      app = tornado.web.Application([
         (r"/", TornadoHandler),
      ])
      app.listen(8000)
      tornado.ioloop.PeriodicCallback(self.__check_online, 2500).start()
      tornado.ioloop.IOLoop.instance().start()

   def is_shooting(self):
      global ServerData
      return ServerData.request_pictures_from_camera and time.time() - ServerData.last_picture_timestamp < 1

   def set_flight(self, flight):
      global ServerData
      ServerData.flight = flight

   def start_shooting(self, cameras_data, flight):
      global ServerData
      if ServerData.request_pictures_from_camera:
         return False

      if not self.is_online('cam1') and not self.is_online('cam2'):
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

   def stop_shooting(self):
      logger.info("Request to stop shooting")
      global ServerData
      ServerData.request_pictures_from_camera = False

   # Both cameras online and not currently requesting pictures
   def is_ready_to_shoot(self):
      global ServerData
      if not self.is_online("cam1"):
         return False
      if not self.is_online("cam2"):
         return False
      return not ServerData.request_pictures_from_camera


   def is_online(self, cam):
      global ServerData
      return ServerData.camera_online_status[cam]

   def __check_online(self):
      self.__check_online_status("cam1")
      self.__check_online_status("cam2")

   ''' Our definition of online '''
   def __is_online(self, cam):
      global ServerData
      return time.time() - ServerData.camera_last_transmission_timestamp[cam] < 5

   def __check_online_status(self, cam):
      global ServerData
      if ServerData.camera_online_status[cam] == True and self.__is_online(cam) == False:
         ServerData.camera_online_status[cam] = False
         logger.debug("Camera is going offline: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_OFFLINE, cam)
         return
      if ServerData.camera_online_status[cam] == False and self.__is_online(cam):
         ServerData.camera_online_status[cam] = True
         logger.debug("Camera is coming online: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_ONLINE, cam)


   def start_server(self, db: DB):
      global ServerData
      ServerData.db = db

      logger.info("Starting camera server")
      _thread.start_new_thread(self.__startHTTP, ())
