from threading import Lock

from database.db import DB
import database.frame_dao as frame_dao
from frame import Frame

from function_timer import timer

import logging
logger = logging.getLogger(__name__)

class CamerasData:
   __mutex = Lock()

   __db = None # type: DB
   __flight = None # type: int

   __frames = {
      'cam1': {},
      'cam2': {}
   }

   __frame_count = {
      'cam1': 0,
      'cam2': 0
   }

   def __init__(self, db: DB, flight: int):
      self.__db = db
      self.__flight = flight
      self.__frames['cam1'] = {}
      self.__frames['cam2'] = {}

   def __acquire_lock(self):
      logger.debug("Acquire lock")
      self.__mutex.acquire()

   def __release_lock(self):
      logger.debug("Release lock")
      self.__mutex.release()

   def add_frame(self, frame: Frame) -> bool:
      logger.debug("add_frame() position " + str(frame.get_position()))
      self.__acquire_lock()
      ''' We require the frames to actually be in order from 1 to infinity '''
      if frame.get_position() > 1 and not self.__frames[frame.get_cam()][frame.get_position() - 1]:
         logger.critical("Missing a frame when adding, can't continue!")
         self.__release_lock()
         return False

      cam = frame.get_cam()
      position = frame.get_position()
      self.__frames[cam][position] = frame
      self.__frame_count[cam] = position
      self.__release_lock()
      return True

   def get_start_timestamp(self):
      logger.debug("get_start_timestamp()")
      self.__acquire_lock()
      try:
         frame1_cam1 = self.get_frame('cam1', 1)
         timestamp_cam1 = frame1_cam1.get_timestamp()
      except IndexError:
         timestamp_cam1 = 0

      try:
         frame1_cam2 = self.get_frame('cam2', 1)
         timestamp_cam2 = frame1_cam2.get_timestamp()
      except IndexError:
         timestamp_cam2 = 0

      self.__release_lock()
      return max(timestamp_cam1 or 0, timestamp_cam2 or 0)

   def get_last_frame(self, cam: str) -> Frame:
      logger.debug("get_last_frame()")
      self.__acquire_lock()
      if self.__frame_count[cam] == 0:
         self.__release_lock()
         return None
      self.__release_lock()
      try:
         return self.get_frame(cam, self.__frame_count[cam])
      except IndexError:
         return None

   def get_frame(self, cam: str, position: int) -> Frame:
      if self.__frames[cam].get(position): return self.__frames[cam][position]
      timestamp = frame_dao.load_timestamp(self.__db, self.__flight, cam, position)
      if timestamp is None:
         raise IndexError("position out of range")
      self.__frames[cam][position] = Frame(self.__flight, cam, position, timestamp, None)
      return self.__frames[cam][position]

   def get_frame_count(self, cam: str):
      return self.__frame_count[cam]

   @timer("Time to load last position")
   def load(self):
      logger.info("Lazy loading flight " + str(self.__flight) + "...")
      for cam in ['cam1', 'cam2']:
         self.__frame_count[cam] = frame_dao.load_frame_count(self.__db, self.__flight, cam)
