import PySide2
from PySide2 import QtCore, QtGui
import os
import cv2 as cv
import time
from database.DB import DB
import database.frame_dao as frame_dao
import numpy as np
import simplejpeg

from function_timer import timer

import logging
logger = logging.getLogger(__name__)

class Video:

   def __init__(self, db: DB, cam, flight, widgetVideo, buttonPlayForward, buttonPlayBackward, buttonPause, buttonFind, buttonForwardStep, buttonBackStep, slider, buttonCopy, labelTime):

      self.__db = db
      self.__flight = flight

      # Frame number in video
      self.current_frame_number = 0

      # Find flag
      self.find = False

      # Motion direction
      self.direction = 0
      self.currently_tracking = 0

      # Currently shooting
      self.shooting = False

      # Forward / Backward flag
      self.forward = True

      # cam1 or cam2
      self.cam = cam

      # Directory of flight
      self.__flight_directory = None

      # Timestamp to start video on, this is the higest number of the two cameras
      self.start_timestamp = 0

      # Ground level, no motion track below this
      self.groundlevel = 400

      self.last_motion_view_frame = 0

      # Lots of widgets
      self.widgetVideo = widgetVideo
      self.buttonPlayForward = buttonPlayForward
      self.buttonPlayForward.clicked.connect(self.__onPlayForward)
      self.buttonPlayBackward = buttonPlayBackward
      self.buttonPlayBackward.clicked.connect(self.__onPlayBackward)
      self.buttonFind = buttonFind
      self.buttonFind.clicked.connect(self.__onFind)
      self.buttonForwardStep = buttonForwardStep
      self.buttonForwardStep.clicked.connect(self.__onForwardStep)
      self.buttonBackStep = buttonBackStep
      self.buttonBackStep.clicked.connect(self.__onBackStep)
      self.buttonPause = buttonPause
      self.buttonPause.clicked.connect(self.__onPause)
      self.slider = slider
      self.slider.sliderMoved.connect(self.__onSliderChanged)
      self.buttonCopy = buttonCopy
      self.buttonCopy.clicked.connect(self.__onCopy)
      self.labelTime = labelTime

      # Timer for playing video
      self.timer = QtCore.QTimer(self.widgetVideo)
      self.timer.timeout.connect(self.__timerplay)

      # Setup worker thread (reason to have this is to utilize multicore)
      self.frame_processing_worker = FrameProcessingWorker(self)

   # Sibling video is the Video instance of the other camera
   def set_sibling_video(self, sibling_video):
      self.sibling_video = sibling_video

   # Reset parameters
   def reset(self):
      self.current_frame_number = 1
      self.find = False
      self.direction = 0

   # Set this Video instance to shooting, mening realtime view of data
   def set_shooting(self, shooting):
      self.direction = 0
      self.shooting = shooting
      if (self.shooting):
         self.buttonPlayForward.setEnabled(False)
         self.buttonPlayBackward.setEnabled(False)
         self.buttonFind.setEnabled(False)
         self.buttonForwardStep.setEnabled(False)
         self.buttonBackStep.setEnabled(False)
         self.buttonPause.setEnabled(False)
         self.slider.setEnabled(False)
         self.buttonCopy.setEnabled(False)

      if (self.shooting == False):
         self.slider.setMinimum(1)
         self.slider.setMaximum(self.cameras_data.get_last_frame(self.cam).get_position())
         self.buttonPlayForward.setEnabled(True)
         self.buttonPlayBackward.setEnabled(True)
         self.buttonFind.setEnabled(True)
         self.buttonForwardStep.setEnabled(True)
         self.buttonBackStep.setEnabled(True)
         self.buttonPause.setEnabled(True)
         self.slider.setEnabled(True)
         self.buttonCopy.setEnabled(True)

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
      frame = frame_dao.load(self.__db, self.__flight, 1 if self.cam == 'cam1' else 2, position)
      if frame is None: return
      image_cv = simplejpeg.decode_jpeg(frame.get_image(), colorspace='GRAY')

      return {"frame_number": position, "timestamp": int(timestamp), "image": image_cv }

   # Set the start timestamp
   def setStartTimestamp(self, start_timestamp):
      self.start_timestamp = start_timestamp

   # Copy button, set the timestamp of the sibling video to this on
   def __onCopy(self):
      timestamp_this = self.cameras_data.get_frame(self.cam, self.current_frame_number).get_timestamp()
      for i in range(1, self.cameras_data.get_last_frame(self.sibling_video.cam).get_position() + 1):
         timestamp_sibling = self.cameras_data.get_frame(self.sibling_video.cam, i).get_timestamp()
         if timestamp_sibling >= timestamp_this:
            break
      self.sibling_video.view_frame(i)
      self.sibling_video.direction = 0

   def __onSliderChanged(self, value):
      self.direction = 0
      self.current_frame_number = value
      self.__update(self.__get_frame(self.cam, self.current_frame_number))
      self.timer.stop()

   def __onPlayForward(self):
      self.direction = 0
      self.find = False
      self.forward = True
      self.timer.start(11)

   def __onPlayBackward(self):
      self.direction = 0
      self.find = False
      self.forward = False
      self.timer.start(11)

   def __onPause(self):
      self.direction = 0
      self.timer.stop()
      self.__update(self.__get_frame(self.cam, self.current_frame_number))

   def __onFind(self):
      self.find = True
      self.forward = True
      self.timer.start(0)

   def __onForwardStep(self):
      self.direction = 0
      if self.current_frame_number < self.cameras_data.get_last_frame(self.cam).get_position():
         self.current_frame_number += 1
      self.timer.stop()
      self.__update(self.__get_frame(self.cam, self.current_frame_number))

   def __onBackStep(self):
      self.direction = 0
      if self.current_frame_number > 1:
         self.current_frame_number -= 1
      self.timer.stop()
      self.__update(self.__get_frame(self.cam, self.current_frame_number))

   def __timerplay(self):
      if self.forward:
         self.current_frame_number += 1
         if self.cameras_data.get_last_frame(self.cam) is None or self.current_frame_number > self.cameras_data.get_last_frame(self.cam).get_position():
            self.current_frame_number = self.cameras_data.get_last_frame(self.cam).get_position()
            self.find = False
            self.timer.stop()
            self.__update(self.__get_frame(self.cam, self.current_frame_number))
      else:
         self.current_frame_number -= 1
         if self.cameras_data.get_last_frame(self.cam) is None or self.current_frame_number < 1:
            self.current_frame_number  =1
            self.find = False
            self.timer.stop()
            self.__update(self.__get_frame(self.cam, self.current_frame_number))

      # Find motion when playing video
      frame = self.__get_frame(self.cam, self.current_frame_number)
      if not frame:
         return
      if self.forward:
         self.frame_processing_worker.wait()
         motion = self.__have_motion(frame['image'])
         if motion is not None and self.find:
            frame['image'] = motion["image"]
            if motion["motion"]:
               self.timer.stop()
               self.__update(frame)

      if self.find and self.current_frame_number & 7 == 1:
         self.__update(frame)
      elif not self.find:
         self.__update(frame)         

   def view_frame(self, frame_number):
      self.current_frame_number = frame_number
      self.__update(self.__get_frame(self.cam, self.current_frame_number))

   def is_analyzer_running(self) -> bool:
      return self.frame_processing_worker.isRunning()

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
      if motion["motion"]:
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

      if self.frame_processing_worker.isRunning():
         logger.error("Analyzer still running on camera " + self.cam)
         return None
 
      image = self.frame_processing_worker.image
      found_motion = False if self.frame_processing_worker.found_motion_position == -1 else True
      found_motion_frame_number = self.frame_processing_worker.found_motion_position

      self.frame_processing_worker.do_processing(image_cv, self.current_frame_number)

      return { "motion": found_motion, "image": image, "frame_number": found_motion_frame_number }

   def __update(self, frame):
      if not frame:
         return

      local_timestamp = frame["timestamp"] - self.start_timestamp
      if (local_timestamp < 0):
         local_timestamp = 0
      self.labelTime.setText(self.__format_time(local_timestamp))

      if (self.shooting):
         self.slider.setSliderPosition(1)
      else:
         self.slider.setSliderPosition(frame["frame_number"])

      # Draw center line
      cv.rectangle(frame["image"], (160, 0), (160, 480), (0, 0, 0), 1)
      # Draw ground level
      cv.rectangle(frame["image"], (0, self.groundlevel), (320, self.groundlevel), (0, 0, 0), 1)

      image_qt = QtGui.QImage(frame["image"], frame["image"].shape[1], frame["image"].shape[0], frame["image"].strides[0], QtGui.QImage.Format_Indexed8)
      self.widgetVideo.setPixmap(QtGui.QPixmap.fromImage(image_qt))

   def __format_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)


''' Worker thread doing the actual analyzing '''
class FrameProcessingWorker(QtCore.QThread):
   def __init__(self, video):
      # Video instance
      self.__video = video

      # Image cv needed for processing
      self.__image_cv = None

      # Frame number for processing
      self.__processing_position = 0

      # Comparision for motion tracking
      self.__comparison_image_cv = None

      # Motion boxes for all frames
      self.__motion_boxes = {}

      # Found motion on position 
      self.found_motion_position = -1

      # Image returned by the have motion
      self.image = None

      # Last frame analyzed
      self.__last_frame_number = 0

      QtCore.QThread.__init__(self)
      self.setObjectName("Analyzer-" + self.__video.cam + "-QThread")

   def do_processing(self, image_cv, processing_position):
      self.__image_cv = image_cv
      self.__processing_position = processing_position
      self.start()

   def run(self):
      self.analyze(self.__video.cam)
    
   @timer("Time to analyze", logging.INFO, identifier='cam', average=1000)
   def analyze(self, cam):
      # We do not want to analyze the same frame twice
      if self.__processing_position == self.__last_frame_number:
         return

      # SEt frame number to -1 to indicate we did not found any motion
      self.found_motion_position = -1

      # Check to see if we are lagging behind
      if self.__last_frame_number + 1 != self.__processing_position:
         logger.warning("Missed frame on camera " + cam + ": " + str(self.__processing_position))
      self.__last_frame_number = self.__processing_position

      start = time.time()

      image_gray_cv = self.__image_cv
      #13 13
      image_blur_cv = cv.GaussianBlur(image_gray_cv, (9, 9), 0)
      found_motion = False

      if self.__comparison_image_cv is not None:

         frame_delta = cv.absdiff(self.__comparison_image_cv, image_blur_cv)
         threshold = cv.threshold(frame_delta, 2, 255, cv.THRESH_BINARY)[1]
         threshold = cv.dilate(threshold, None, iterations=3)
         (self.__motion_boxes[self.__processing_position], _) = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
#            print len(self.__motion_boxes[self.current_frame_number])

         #DEBUG  MOTION TRACK
#            if len(self.__motion_boxes[self.current_frame_number]) > 30:
         if False:
            if (self.__video.direction == 0):
               found_motion = True
               self.__video.direction = 90 * 6
         else:
            for c in self.__motion_boxes[self.__processing_position]:
               (x, y, w, h) = cv.boundingRect(c)

               # Set ground level
               if y > self.__video.groundlevel:
                  continue

               #15
               if cv.contourArea(c) < 135:
                  continue
               if cv.contourArea(c) > 10000:
                  continue
               found_center_line = True if x < 160 and x + w > 160 else False

               cv.rectangle(image_gray_cv, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 0, 0), 2)

               if found_center_line and self.__processing_position > 4 and self.__video.currently_tracking == 0:
                  # Check previous motion boxes
                  last_box = Rect()
                  test_frames = 10
                  while True:
                     if (test_frames > 10):
                        logger.info("Need to test frames further back(" + str(test_frames)+ ") on frame: " + str(self.__processing_position))
                     self.__video.direction = self.__check_overlap_previous(x, y, w, h, x, w, self.__processing_position - 1, test_frames, last_box)

                     # You need to run fairly straight to register
                     if (abs(x - last_box.x) < abs(y - last_box.y) * 5):
                        self.__video.direction = 0

                     if (self.__video.direction != 0):
                        found_motion = True
#                        print (cv.contourArea(c))
                        if last_box.x > 70 and last_box.x < 230:
                           test_frames += 10
                           if test_frames < 40: 
                              self.__video.direction = 0
                              found_motion = False
                              continue
                        break
                     else:
                        pass
                        found_motion = False
                        break
                  if found_motion: break
               else:
                  pass
                  found_motion = False

      if found_motion:
         logger.info("Motion found: area: " + str(cv.contourArea(c)))

      self.__comparison_image_cv = image_blur_cv
      self.image = image_gray_cv
      if (found_motion):
         self.found_motion_position = self.__processing_position

   def __check_overlap_previous(self, x, y, w, h, x1, w1, frame_number, iterations, rect):
#      print "check overlap: " + str(frame_number) + " iteration: " + str(iterations)
      if not frame_number in self.__motion_boxes:
         return 0
      for c2 in self.__motion_boxes[frame_number]:
         (x2, y2, w2, h2) = cv.boundingRect(c2)
         rect.x = x2
         rect.y = y2
         rect.w = w2
         rect.h = h2

         if cv.contourArea(c2) < 15:
            continue
         if cv.contourArea(c2) > 10000:
            continue

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
         if iterations == 0 or x2 < 20 or x2 + w2 > 300:
            if x1 + w1 < x2 + w2:
               return -1
            else:
               return 1
         return self.__check_overlap_previous(x2, y2, w2, h2, x1, w1, frame_number - 1, iterations -1, rect)
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