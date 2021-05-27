from threading import Lock
import time

from database.DB import DB
import database.frame_dao as frame_dao
from Frame import Frame

import logging
logger = logging.getLogger(__name__)

class CamerasData:
   __mutex = Lock()

   __frames = {
      'cam1': {},
      'cam2': {}
   }

   def __init__(self):
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
      if frame.get_position() > 1 and not self.__frames['cam' + str(frame.get_camera())][frame.get_position() - 1]:
         logger.critical("Missing a frame when adding, can't continue!")
         self.__release_lock()
         return False

      self.__frames['cam' + str(frame.get_camera())][frame.get_position()] = frame
      self.__release_lock()
      return True

   def get_start_timestamp(self):
      logger.debug("get_start_timestamp()")
      self.__acquire_lock()
      timestamp_cam1 = self.__frames['cam1'][1].get_timestamp() if 1 in self.__frames['cam1'] else 0
      timestamp_cam2 = self.__frames['cam2'][1].get_timestamp() if 1 in self.__frames['cam2'] else 0
      self.__release_lock()
      return max(timestamp_cam1, timestamp_cam2)

   def get_last_frame(self, cam: str) -> Frame:
      logger.debug("get_last_frame()")
      self.__acquire_lock()
      if len(self.__frames[cam]) == 0:
         self.__release_lock()
         return None
      frame = self.__frames[cam][len(self.__frames[cam])]
      self.__release_lock()
      return frame

   def get_timestamp_from_position(self, cam: str, position: int) -> int:
      if not position in self.__frames[cam]: return 0
      return max(self.__frames[cam][position].get_timestamp(), 0)

   def get_frame(self, cam: str, position: int) -> Frame:
      return self.__frames[cam][position] if position in self.__frames[cam] else None

   def get_frames_length(self, cam: str):
      return len(self.__frames[cam])

   def load(self, db: DB, flight):
      start = time.time()
      logger.info("Loading flight " + str(flight) + "...")
      for cam in [1, 2]:
         self.__frames['cam' + str(cam)] = {}
         rows = frame_dao.load_flight_timestammps(db, flight, cam)
         for row in rows:
            self.__frames['cam' + str(cam)][row[0]] = Frame(flight, cam, row[0], row[1], None)
      logger.info("Loading flight done: " + format(time.time() - start, ".3f") + "s")
