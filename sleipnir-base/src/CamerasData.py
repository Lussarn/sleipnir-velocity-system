from threading import Thread, Lock
import os


class FrameData():

   def __init__(self):
      self.frames_2_timestamps = {}

class CamerasData:
   mutex = Lock()

   def __init__(self):
      self.frame_data = {}
      self.frame_data["cam1"] = FrameData()
      self.frame_data["cam2"] = FrameData()

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

   def load(self, camdir_base, flight_number):
      for cam in ["cam1", "cam2"]:
         self.frame_data[cam].frames_2_timestamps = {}

         filename = os.path.join(camdir_base, str(flight_number), cam, "timestamps.txt")
         if not os.path.exists(filename):
            self.frame_data["cam1"].frames_2_timestamps = {}
            self.frame_data["cam2"].frames_2_timestamps = {}
            return False

         with open(filename) as f:
            content = f.readlines()

         for data in content:
            data = data.split()
            self.frame_data[cam].frames_2_timestamps[int(data[0])] = int(data[1])

      return True