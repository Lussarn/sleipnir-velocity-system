from threading import Lock
import time

from database.DB import DB
import database.frame_dao as frame_dao

import logging
logger = logging.getLogger(__name__)

class FrameData():

   def __init__(self):
      self.frames_2_timestamps = {}

class CamerasData:
   mutex = Lock()

   def __init__(self):
      self.frame_data = {}
      self.frame_data["cam1"] = FrameData()
      self.frame_data["cam2"] = FrameData()
      self.last_served_frame = {}
      self.last_served_frame["cam1"] = 0
      self.last_served_frame["cam2"] = 0

   def add_frame(self, cam, frame_number, timestamp):
      self.mutex.acquire()
      self.frame_data[cam].frames_2_timestamps[frame_number] = timestamp
      self.mutex.release()

   def get_start_timestamp(self):
      self.mutex.acquire()
      timestamp_cam1 = 0
      if 1 in self.frame_data["cam1"].frames_2_timestamps:
         timestamp_cam1 = self.frame_data["cam1"].frames_2_timestamps[1]
      timestamp_cam2 = 0
      if 1 in self.frame_data["cam2"].frames_2_timestamps:
         timestamp_cam2 = self.frame_data["cam2"].frames_2_timestamps[1]
      self.mutex.release()
      return max(timestamp_cam1, timestamp_cam2)

   def get_next_frame(self, cam):
      self.mutex.acquire()
      last_frame = len(self.frame_data[cam].frames_2_timestamps)
      self.mutex.release()
      next_frame = self.last_served_frame[cam] + 1
      # How many frames are we allowed to lag
      if abs(last_frame - self.last_served_frame[cam]) > 30:         
         next_frame = last_frame
         logger.warning("Camera " + cam + " lagging behind, reseting next_frame to last_frame")
      self.last_served_frame[cam] = min(last_frame, next_frame)
      return self.last_served_frame[cam]

   def get_last_frame(self, cam):
      self.mutex.acquire()
      frame_number =  len(self.frame_data[cam].frames_2_timestamps)
      self.mutex.release()
      return frame_number

   def get_timestamp_from_frame_number(self, cam, frame_number):
      if not frame_number in self.frame_data[cam].frames_2_timestamps:
         return 0
      return max(self.frame_data[cam].frames_2_timestamps[frame_number], 0)

   def is_data_ok(self):
      return len(self.frame_data["cam1"].frames_2_timestamps) >= 90 and len(self.frame_data["cam2"].frames_2_timestamps) >= 90

   def load(self, db: DB, flight_number):
      start = time.time()
      logger.info("Loading flight number " + str(flight_number) + "...")
      for cam in [1, 2]:
         self.frame_data['cam' + str(cam)] = FrameData()
         rows = frame_dao.load_flight_timestammps(db, flight_number, cam)
         f_2_ts = {}
         for row in rows: f_2_ts[row[0]] = row[1]
         self.frame_data['cam' + str(cam)].frames_2_timestamps = f_2_ts
      end = time.time()
      logger.info("Loading flight done: " + format(end-start, ".3f") + "s")
