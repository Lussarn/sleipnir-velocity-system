from PySide2 import QtCore, QtGui
import cv2 as cv
from database.DB import DB
import database.frame_dao as frame_dao
import simplejpeg
import math

from Frame import Frame
from function_timer import timer

import logging
logger = logging.getLogger(__name__)

class Video:
   def __init__(self, db: DB, cam: str, flight: int, max_dive_angle: float, blur_strength: int, widgetVideo, labelTime):

      self.__db = db
      self.__flight = flight
      self.__max_dive_angle = max_dive_angle
      self.__blur_strength = blur_strength

      # Frame number in video
      self.current_frame_number = 0

      # Motion direction
      self.direction = 0
      self.currently_tracking = 0

      # cam1 or cam2
      self.cam = cam

      # Timestamp to start video on, this is the higest number of the two cameras
      self.start_timestamp = 0

      # Ground level, no motion track below this
      self.groundlevel = 400

      # Lots of widgets
      self.widgetVideo = widgetVideo
      self.labelTime = labelTime

      # Setup worker thread (reason to have this is to utilize multicore)
      self.analyzer_worker = AnalyzerWorker(self.cam)

   # Reset parameters
   def reset(self):
      self.current_frame_number = 1
      self.direction = 0

   # Returns current frame number of video
   def get_current_frame_number(self):
      return self.current_frame_number

   # Set flight number
   def set_flight(self, flight):
      self.__flight = flight

   # Returns a video frame as a cv image and it's timestamp
   @timer("Time to read jpeg", logging.INFO, identifier='cam', average=1000)
   def __get_frame(self, cam, position):
      timestamp = self.cameras_data.get_frame(cam, position).get_timestamp()
      frame = frame_dao.load(self.__db, self.__flight, self.cam, position)
      if frame is None: return
      image_cv = simplejpeg.decode_jpeg(frame.get_image(), colorspace='GRAY')

      return {"frame_number": position, "timestamp": int(timestamp), "image": image_cv }

   # Set the start timestamp
   def setStartTimestamp(self, start_timestamp):
      self.start_timestamp = start_timestamp

   def view_frame(self, frame_number):
      self.current_frame_number = frame_number
      self.__update(self.__get_frame(self.cam, self.current_frame_number))

   def is_analyzer_running(self) -> bool:
      return self.analyzer_worker.isRunning()

   def view_frame_motion_track(self, frame_number, live_preview = True):
      if self.currently_tracking > 0: self.currently_tracking -= 1

      self.current_frame_number = frame_number
      frame = self.__get_frame(self.cam, self.current_frame_number)
      if not frame:
         return
      motion = self.__have_motion(frame["image"])
      if (motion is None):
         return None

      frame['image'] = motion["image"]
      # Only show every 3 frame
      if live_preview and self.current_frame_number % 3 == 0:
         self.__update(frame)
      if self.currently_tracking == 0 and motion["motion"]:
         self.currently_tracking = 90 * 6
         return { 
            "frame_number": motion["frame_number"], 
            "direction": self.direction / (1 if self.direction == 0 else abs(self.direction)) }
      return None

   # Find if an image have motion
   def __have_motion(self, image_cv):
      if (image_cv is None):
         logger.error("Image lost on camera " + self.cam + " image_cv == None")
         return None

      if self.analyzer_worker.isRunning():
         logger.error("Analyzer still running on camera " + self.cam)
         return None
 
      msg = self.analyzer_worker.get_analyzer_done_message()

      image = msg.get_image()
      self.direction = msg.get_direction()
      found_motion = msg.have_motion()
      found_motion_position = msg.get_position()

      msg = AnalyzerDoMessage(image_cv, self.current_frame_number, self.groundlevel, self.__max_dive_angle, self.__blur_strength)
      self.analyzer_worker.do_processing(msg)

      return { 
         "motion": found_motion, 
         "image": image, 
         "frame_number": found_motion_position
         }

   def __update(self, frame :Frame):
      if not frame:
         return

      local_timestamp = frame["timestamp"] - self.start_timestamp
      if (local_timestamp < 0):
         local_timestamp = 0
      self.labelTime.setText(self.__format_time(local_timestamp))

      # Draw center line
      cv.rectangle(frame["image"], (160, 0), (160, 480), (0, 0, 0), 1)
      # Draw ground level
      cv.rectangle(frame["image"], (0, self.groundlevel), (320, self.groundlevel), (0, 0, 0), 1)

      image_qt = QtGui.QImage(frame["image"], frame["image"].shape[1], frame["image"].shape[0], frame["image"].strides[0], QtGui.QImage.Format_Indexed8)
      self.widgetVideo.setPixmap(QtGui.QPixmap.fromImage(image_qt))

   def __format_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)

class AnalyzerDoMessage:
   __image = None
   __position = 0
   __ground_level = 0
   __max_dive_angle = 0
   __blur_strength = 0

   def __init__(self, image, position, ground_level, max_dive_angle, blur_strength):
      self.__image = image
      self.__position = position
      self.__ground_level = ground_level
      self.__max_dive_angle = max_dive_angle
      self.__blur_strength = blur_strength
   def get_image(self):
      return self.__image
   def get_position(self):
      return self.__position
   def get_ground_level(self):
      return self.__ground_level
   def get_max_dive_angle(self):
      return self.__max_dive_angle
   def get_blur_strength(self):
      return self.__blur_strength

class AnalyzerDoneMessage:
   __image = None
   __direction = 0
   __position = -1

   def __init__(self, image, direction, position):
      self.__image = image
      self.__direction = direction
      self.__position = position

   def get_image(self):
      return self.__image
   def get_direction(self):
      return self.__direction
   def get_position(self):
      return self.__position
   def have_motion(self):
      return self.__position != -1

''' Worker thread doing the actual analyzing '''
class AnalyzerWorker(QtCore.QThread):
   def __init__(self, cam: str):
      # "cam1" or "cam2"
      self.__cam = cam

      # Comparision for motion tracking
      self.__comparison_image_cv = None

      # Motion boxes for all frames
      self.__motion_boxes = {}

      # Last frame analyzed
      self.__last_position = 0

      self.__analyzer_do_message = None
      # Message to transfer back to main program
      self.__analyzer_done_message = AnalyzerDoneMessage(None, 0, -1)

      QtCore.QThread.__init__(self)
      self.setObjectName("Analyzer-" + self.__cam + "-QThread")

   def get_analyzer_done_message(self):
      return self.__analyzer_done_message

   def do_processing(self, analyzer_do_message: AnalyzerDoMessage):
      self.__analyzer_do_message = analyzer_do_message
      self.start()

   def run(self):
      self.analyze(self.__cam)
    
   @timer("Time to analyze", logging.INFO, identifier='cam', average=1000)
   def analyze(self, cam):
      position = self.__analyzer_do_message.get_position()

      # We do not want to analyze the same frame twice
      if position == self.__last_position:
         return

      # Check to see if we are lagging behind
      if self.__last_position + 1 != position:
         logger.warning("Missed frame on camera " + cam + ": " + str(position))
      self.__last_position = position

      __image_gray_cv = self.__analyzer_do_message.get_image()
      blur = int(5 +  self.__analyzer_do_message.get_blur_strength() * 2)
      image_blur_cv = cv.GaussianBlur(__image_gray_cv, (blur, blur), 0)

      direction = 0
      if self.__comparison_image_cv is not None:

         frame_delta = cv.absdiff(self.__comparison_image_cv, image_blur_cv)
         threshold = cv.threshold(frame_delta, 2, 255, cv.THRESH_BINARY)[1]
         threshold = cv.dilate(threshold, None, iterations=3)
         (self.__motion_boxes[position], _) = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

         for c in self.__motion_boxes[position]:
            (x, y, w, h) = cv.boundingRect(c)

            # No tracking below ground level
            if y + h > self.__analyzer_do_message.get_ground_level(): continue

            if cv.contourArea(c) < 135 or cv.contourArea(c) > 10000: continue

            found_center_line = True if x < 160 and x + w > 160 else False
            cv.rectangle(__image_gray_cv, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 0, 0), 2)

            direction = 0
            if found_center_line and position > 4:
               # Check previous motion boxes
               last_box = Rect()
               test_frames = 10
               while True:
                  if (test_frames > 10):
                     logger.info("Need to test frames further back(" + str(test_frames)+ ") on frame: " + str(position))
                  direction = self.__check_overlap_previous(x, y, w, h, x, w, position - 1, test_frames, last_box)

                  # The 0.0000001 will remove a division by zero if x - last_box.x is 0
                  dive_angle = math.atan(abs(y - last_box.y) / (abs(x - last_box.x) + 0.0000001) ) * 180 / math.pi
                  if  dive_angle > self.__analyzer_do_message.get_max_dive_angle():
                     logger.debug("Max dive angle of " + str(self.__analyzer_do_message.get_max_dive_angle()) + "° exceeded on position " + str(position) + " (" +  "{:.2f}".format(dive_angle)+ "°)")
                     direction = 0


                  # Definitely no hit
                  if direction == 0: break

                  # If the moving object is not passed about half the screen, test more further back, to raise confidence
                  if last_box.x + (last_box.w / 2) > 80 and last_box.x + (last_box.w / 2) < 240 and test_frames < 30:
                     test_frames += 10
                     continue

                  # We have a registered hit!
                  break
               if direction != 0: break

      self.__comparison_image_cv = image_blur_cv
      if direction != 0:
         logger.info("Motion found: area: " + str(cv.contourArea(c)))

      self.__analyzer_done_message = AnalyzerDoneMessage(
         __image_gray_cv, 
         direction,
         position if direction != 0 else -1)

   def __check_overlap_previous(self, x, y, w, h, x1, w1, position, iterations, rect):
#      print "check overlap: " + str(frame_number) + " iteration: " + str(iterations)
      if not position in self.__motion_boxes:
         return 0
      for c2 in self.__motion_boxes[position]:
         (x2, y2, w2, h2) = cv.boundingRect(c2)
         rect.x = x2
         rect.y = y2
         rect.w = w2
         rect.h = h2

         if cv.contourArea(c2) < 15 or cv.contourArea(c2) > 10000: continue

         if x == x2 and y == y2 and w == w2 and h == h2 :
            continue

         # Sanity on size
         if w < 5 or h < 5 or w > 100 or h > 100:
            continue

         # the sizes of the boxes can't be too far off
         d1 = float(w * h)
         d2 = float(w2 * h2)
         diff = min(d1, d2) / max(d1, d2)
         if diff < 0.3:
            continue
 #        print "size diff: " + str(diff)
 
         if (self.__overlap_box(x, y, w, h, x2, y2, w2, h2) == 0):
            continue

         # if iterations is zero or object is coming to close to the side
         if iterations == 0 or x2 == 0 or x2 + w2 >= 320:
            if x1 + w1 < x2 + w2:
               return -1
            else:
               return 1
         return self.__check_overlap_previous(x2, y2, w2, h2, x1, w1, position - 1, iterations -1, rect)
      return 0

   # Return 0 on non overlap
   def __overlap_box(self, x, y, w, h, x2, y2, w2, h2):
      if (x + w < x2):    # c is left of c2
         return 0
      if (x > x2 + w2):   # c is right of c2
         return 0
      if (y + h < y2):    # c is above c2
         return 0
      if (y > y2 + h2):   # c is below c2                        
         return 0

      # Find direction from first frame
      if x + w < x2 + w2:
         return -1
      else:
         return 1   
   
class Rect:
   x = 0
   y = 0
   w = 0
   h = 0

