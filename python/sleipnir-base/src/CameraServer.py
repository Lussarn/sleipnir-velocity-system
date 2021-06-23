#!/bin/env python

import _thread
import time
import logging
import asyncio

import tornado.ioloop
import tornado.web
from CamerasData import CamerasData

import Event
from database.DB import DB
import database.frame_dao as frame_dao
from Frame import Frame
from function_timer import timer

''' Set logger on third party modules '''
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger('tornado.access').disabled = True

logger = logging.getLogger(__name__)

'''
CameraServer emits the following events

CameraServer.EVENT_CAMERA_ONLINE cam : str        : Camera have come online
CameraServer.EVENT_CAMERA_OFFLINE cam : str       : Camera have gone offline
CameraServer.EVENT_NEW_FRAME frame : Frame        : A new picture have arrived from the camera
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

      # Camera Frames
      self.cameras_data = None

      # Last transmission
      self.camera_last_seen = {"cam1": 0, "cam2": 0}

      # onlide status, we use a state for this so we can seend an event if state changes
      self.camera_online_status = {"cam1": False, "cam2": False}

''' Request Handler '''
class RequestHandler(tornado.web.RequestHandler):
   def log_message(self, format, *args):
      pass

   def initialize(self,server_state):
      self.__server_state = server_state

   @timer("Http POST", logging.INFO, identifier=None, average=1000)
   def post(self):
      action = self.get_argument("action", None, True)

      ''' startcamera action '''
      if (action == "startcamera"):
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("startcamera unknown camera: " + cam)
            return

         self.__server_state.camera_last_seen[cam] = time.time()

         if (self.__server_state.request_pictures_from_camera):
            self.__send_200("OK-START")
         else:
            self.__send_200("OK-STOP")
         pass

      ''' uploadframe action '''
      if (action == "uploadframe"):
         cam = self.get_argument("cam", None, True)
         if cam != "cam1" and cam != "cam2":
            logger.info("uploadframe unknown camera id: " + cam)
            return

         self.__server_state.camera_last_seen[cam] = time.time()

         if (self.__server_state.request_pictures_from_camera):
            frame = Frame(
               self.__server_state.flight,
               cam,
               int(self.get_argument("position", None, True)),
               int(self.get_argument("timestamp", None, True)),
               self.request.body
            )

            ''' Store to SQLite Database '''
            frame_dao.store(self.__server_state.db, frame)

            ''' Clear the image for memory reasons '''
            frame.set_image(None)
            self.__server_state.cameras_data.add_frame(frame)
            ''' Emit new frame event '''
            Event.emit(CameraServer.EVENT_NEW_FRAME, frame)

            self.__send_200("OK-CONTINUE")
         else:
            self.__send_200("OK-STOP")

   def __send_200(self, msg):
      self.set_status(200)
      self.set_header('Content-Type', 'text/plain')
      payload = msg.encode('ASCII')
      self.write(payload)


''' Server '''
class CameraServer:
   EVENT_CAMERA_ONLINE  = "cameraserver.camera_online"
   EVENT_CAMERA_OFFLINE = "cameraserver.camera_offline"
   EVENT_NEW_FRAME      = "cameraserver.new_frame"

   def __init__(self):
      self.__server_state = ServerState()

   def __startHTTP(self) -> None:
      asyncio.set_event_loop(asyncio.new_event_loop())
      app = tornado.web.Application([
         (r"/", RequestHandler, dict(server_state=self.__server_state)),
      ])
      app.listen(8000)
      tornado.ioloop.PeriodicCallback(self.__check_online, 2500).start()
      tornado.ioloop.IOLoop.instance().start()

   def start_server(self, db :DB) -> None:
      self.__server_state.db = db
      logger.info("Starting camera server")
      _thread.start_new_thread(self.__startHTTP, ())

   ''' Definition of is_shooting '''
   def __is_shooting(self, cam :str) -> bool:
      return time.time() - self.__server_state.camera_last_seen[cam] < 1

   ''' public is_shooting api '''
   def is_shooting(self) -> bool:
      return self.__server_state.request_pictures_from_camera and (self.__is_shooting('cam1') or self.__is_shooting('cam2'))

   ''' start requesting pictures from camera '''
   def start_shooting(self, flight :int, cameras_data :CamerasData) -> None:
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

      self.__server_state.flight = flight
      self.__server_state.cameras_data = cameras_data
      self.__server_state.request_pictures_from_camera = True
      return True

   ''' Request to stop the cameras from taking pictures '''
   def stop_shooting(self) -> None:
      logger.info("Request to stop shooting")
      self.__server_state.request_pictures_from_camera = False

   ''' Both cameras online and not currently requesting pictures '''
   def is_ready_to_shoot(self) -> bool:
      if not self.is_online("cam1"):
         return False
      if not self.is_online("cam2"):
         return False
      return not self.__server_state.request_pictures_from_camera

   ''' public online api '''
   def is_online(self, cam : str) -> bool:
      return self.__server_state.camera_online_status[cam]

   ''' Our definition of online '''
   def __is_online(self, cam : str) -> bool:
      return time.time() - self.__server_state.camera_last_seen[cam] < 5

   ''' Make an online sweep on the cameras '''
   def __check_online(self) -> None:
      self.__check_online_status("cam1")
      self.__check_online_status("cam2")

   ''' Check a single camera for being online '''
   def __check_online_status(self, cam : str) -> None:
      if self.__server_state.camera_online_status[cam] == True and self.__is_online(cam) == False:
         self.__server_state.camera_online_status[cam] = False
         logger.debug("Camera is going offline: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_OFFLINE, cam)
         return
      if self.__server_state.camera_online_status[cam] == False and self.__is_online(cam):
         self.__server_state.camera_online_status[cam] = True
         logger.debug("Camera is coming online: " + cam)
         Event.emit(CameraServer.EVENT_CAMERA_ONLINE, cam)
