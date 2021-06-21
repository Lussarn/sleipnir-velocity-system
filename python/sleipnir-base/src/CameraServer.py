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

'''
CameraServer emits the following events

CameraServer.EVENT_CAMERA_ONLINE cam : str        : Camera have come online
CameraServer.EVENT_CAMERA_OFFLINE cam : str       : Camera have gone offline
'''

''' Server state '''
class ServerState:
   def __init__(self):
      # Sleipnir database
      self.db = None

      # flight number
      self.flight = 1

      # Server is telling camera to start stop sending pictures
      self.request_pictures_from_camera = False

      # Timestamp of last picture
      self.last_picture_timestamp = 0

      # Camera Frames
      self.cameras_data = None

      # Last transmission
      self.camera_last_transmission_timestamp = {"cam1": 0, "cam2": 0}

      # onlide status
      self.camera_online_status = {"cam1": False, "cam2": False}

      # logs
      self.last_log_message_cam_asking_to_start = {'cam1': 0, 'cam2': 0}

''' Request Handler '''
class RequestHandler(tornado.web.RequestHandler):
   def log_message(self, format, *args):
      pass

   def initialize(self,server_state):
      self.__server_state = server_state

   @timer("Http POST", logging.INFO, identifier=None, average=1000)
   def post(self):
      action = self.get_argument("action", None, True)

      cam = ""
      if (action == "startcamera"):
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera: " + cam)
            return

         if cam == "cam1" or cam == "cam2":
            self.__server_state.camera_last_transmission_timestamp[cam] = time.time()

         if (time.time() -  self.__server_state.last_log_message_cam_asking_to_start[cam] > 10):
            logger.info("Camera " + cam + " is online and asking to start")
            self.__server_state.last_log_message_cam_asking_to_start[cam] = time.time()

         if (self.__server_state.request_pictures_from_camera):
            self.send200("OK-START")
         else:
            self.send200("OK-STOP")
         pass

      if (action == "uploadframe"):
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("Uploadframe unknown camera id: " + cam)
            return

         self.__server_state.camera_last_transmission_timestamp[cam] = time.time()

         position = int(self.get_argument("position", None, True))
         timestamp = int(self.get_argument("timestamp", None, True))
         self.__server_state.last_picture_timestamp = time.time()

         image = self.request.body

         frame = Frame(
            self.__server_state.flight,
            1 if cam == 'cam1' else 2,
            position,
            timestamp,
            image
         )
         frame_dao.store(self.__server_state.db, frame)

         ''' Clear the image for memory reasons '''
         frame.set_image(None)
         if not self.__server_state.cameras_data.add_frame(frame):
            logger.critical("Shooting stoped after failed add frame!")
            self.__server_state.camera_server.stop_shooting()

         if (self.__server_state.request_pictures_from_camera):
            self.send200("OK-CONTINUE")
         else:
            self.send200("OK-STOP")

   def send200(self, msg):
      self.set_status(200)
      self.set_header('Content-Type', 'text/plain')
      payload = msg.encode('ASCII')
      self.write(payload)


''' Server '''
class CameraServer:
   EVENT_CAMERA_ONLINE = "cameraserver.camera_online"
   EVENT_CAMERA_OFFLINE = "cameraserver.camera_offline"

   def __init__(self):
      self.__server_state = ServerState()

   def __startHTTP(self):
      asyncio.set_event_loop(asyncio.new_event_loop())
      app = tornado.web.Application([
         (r"/", RequestHandler, dict(server_state=self.__server_state)),
      ])
      app.listen(8000)
      tornado.ioloop.PeriodicCallback(self.__check_online, 2500).start()
      tornado.ioloop.IOLoop.instance().start()

   def start_server(self, db: DB):
      self.__server_state.db = db
      logger.info("Starting camera server")
      _thread.start_new_thread(self.__startHTTP, ())

   ''' Definition of is_shooting '''
   def __is_shooting(self, cam):
      return time.time() - self.__server_state.camera_last_transmission_timestamp[cam] < 1

   ''' public api '''
   def is_shooting(self):
      return self.__server_state.request_pictures_from_camera and (self.__is_shooting('cam1') or self.__is_shooting('cam2'))

   def set_flight(self, flight):
      self.__server_state.flight = flight

   def start_shooting(self, cameras_data, flight):
      if self.__server_state.request_pictures_from_camera:
         return False

      if not self.is_online('cam1') and not self.is_online('cam2'):
         logger.error("Unable to start shooting because camera is not online")
         return False

      try:
         start = time.time()
         logger.info("Deleting old frames and announcements...")
         frame_dao.delete_flight(self.__server_state.db, flight)
         logger.info("Time to remove pictures: " + format(time.time() - start, ".3f") + "s")
      except Exception as e:
         logger.error(str(e))
         return

      self.__server_state.cameras_data = cameras_data
      self.__server_state.request_pictures_from_camera = True
      return True

   def stop_shooting(self):
      logger.info("Request to stop shooting")
      self.__server_state.request_pictures_from_camera = False

   # Both cameras online and not currently requesting pictures
   def is_ready_to_shoot(self):
      if not self.is_online("cam1"):
         return False
      if not self.is_online("cam2"):
         return False
      return not self.__server_state.request_pictures_from_camera


   ''' public online api '''
   def is_online(self, cam):
      return self.__server_state.camera_online_status[cam]

   ''' Our definition of online '''
   def __is_online(self, cam):
      return time.time() - self.__server_state.camera_last_transmission_timestamp[cam] < 5

   ''' Make an online sweep on the cameras '''
   def __check_online(self):
      self.__check_online_status("cam1")
      self.__check_online_status("cam2")

   ''' Check a single camera for being online '''
   def __check_online_status(self, cam):
      if self.__server_state.camera_online_status[cam] == True and self.__is_online(cam) == False:
         self.__server_state.camera_online_status[cam] = False
         logger.debug("Camera is going offline: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_OFFLINE, cam)
         return
      if self.__server_state.camera_online_status[cam] == False and self.__is_online(cam):
         self.__server_state.camera_online_status[cam] = True
         logger.debug("Camera is coming online: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_ONLINE, cam)



