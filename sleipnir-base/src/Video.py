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

      # performance statistics
      self.__stat_jpeg_read_number_of_frames = 0
      self.__stat_jpeg_read_accumulated_time = 0

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
         self.slider.setMaximum(self.cameras_data.get_last_frame(self.cam))
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
   def __get_frame(self, frame_number):
      start = time.time()
      timestamp = self.cameras_data.get_timestamp_from_frame_number(self.cam, frame_number)
      frame = frame_dao.load(self.__db, self.__flight, 1 if self.cam == 'cam1' else 2, frame_number)
      if frame is None: return
      image_cv = simplejpeg.decode_jpeg(frame.get_image(), colorspace='GRAY')

      # statistics logging
      self.__stat_jpeg_read_accumulated_time += (time.time() - start)
      self.__stat_jpeg_read_number_of_frames += 1
      if self.__stat_jpeg_read_number_of_frames % 1000 == 0:
         logger.info("Time to read jpeg " + self.cam + ": " + str(int(self.__stat_jpeg_read_accumulated_time / self.__stat_jpeg_read_number_of_frames * 1000000)/1000) + "ms")
         self.__stat_jpeg_read_accumulated_time = 0
         self.__stat_jpeg_read_number_of_frames = 0

      return {"frame_number": frame_number, "timestamp": int(timestamp), "image": image_cv }

   # Set the start timestamp
   def setStartTimestamp(self, start_timestamp):
      self.start_timestamp = start_timestamp

   # Copy button, set the timestamp of the sibling video to this on
   def __onCopy(self):
      timestamp_this = self.cameras_data.get_timestamp_from_frame_number(self.cam, self.current_frame_number)
      for i in range(1, self.cameras_data.get_last_frame(self.sibling_video.cam) + 1):
         timestamp_sibling = self.cameras_data.get_timestamp_from_frame_number(self.sibling_video.cam, i)
         if timestamp_sibling >= timestamp_this:
            break
      self.sibling_video.view_frame(i)
      self.sibling_video.direction = 0

   def __onSliderChanged(self, value):
      self.direction = 0
      self.current_frame_number = value
      self.__update(self.__get_frame(self.current_frame_number))
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
      self.__update(self.__get_frame(self.current_frame_number))

   def __onFind(self):
      self.find = True
      self.forward = True
      self.timer.start(0)

   def __onForwardStep(self):
      self.direction = 0
      if self.current_frame_number < self.cameras_data.get_last_frame(self.cam):
         self.current_frame_number += 1
      self.timer.stop()
      self.__update(self.__get_frame(self.current_frame_number))

   def __onBackStep(self):
      self.direction = 0
      if self.current_frame_number > 1:
         self.current_frame_number -= 1
      self.timer.stop()
      self.__update(self.__get_frame(self.current_frame_number))

   def __timerplay(self):
      if self.forward:
         self.current_frame_number += 1
         if self.current_frame_number > self.cameras_data.get_last_frame(self.cam):
            self.current_frame_number = self.cameras_data.get_last_frame(self.cam)
            self.find = False
            self.timer.stop()
            self.__update(self.__get_frame(self.current_frame_number))
      else:
         self.current_frame_number -= 1
         if (self.current_frame_number < 1):
            self.current_frame_number  =1
            self.find = False
            self.timer.stop()
            self.__update(self.__get_frame(self.current_frame_number))

      # Find motion when playing video
      frame = self.__get_frame(self.current_frame_number)
      if not frame:
         return
      if self.forward:
         motion = self.have_motion(frame['image'])
         if self.find:
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
      self.__update(self.__get_frame(self.current_frame_number))

   def view_frame_motion_track(self, frame_number, live_preview = True):
      self.current_frame_number = frame_number
      frame = self.__get_frame(self.current_frame_number)
      if not frame:
         return
      motion = self.have_motion(frame["image"])
      if (motion is None):
         return None

      frame['image'] = motion["image"]
      # Only show every 3 frame
      if live_preview and self.current_frame_number % 3 == 0:
         self.__update(frame)
      if motion["motion"]:
         return { "frame_number": motion["frame_number"], "direction": self.direction / abs(self.direction) }
      return None

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

   # Find if an image have motion
   def have_motion(self, image_cv):
      if (image_cv is None):
         logger.error("Image lost on camera " + self.cam + " image_cv == None")
         return

      self.frame_processing_worker.wait()
      image = self.frame_processing_worker.image
      found_motion = self.frame_processing_worker.found_motion
      found_motion_frame_number = self.frame_processing_worker.found_motion_frame_number

      if self.direction < 0: self.direction +=1
      if self.direction > 0: self.direction -=1

      self.frame_processing_worker.do_processing(image_cv, self.current_frame_number)

      return { "motion": found_motion, "image": image, "frame_number": found_motion_frame_number }




class FrameProcessingWorker(QtCore.QThread):
   def __init__(self, video):
      # Video instance
      self.video = video

      # Image cv needed for processing
      self.__image_cv = None

      # Frame number for processing
      self.__processing_frame_number = 0

      # Comparision for motion tracking
      self.__comparison_image_cv = None

      # Motion boxes for all frames
      self.__motion_boxes = {}

      # Found motion on frame number
      self.found_motion_frame_number = 0

      # Image returned by the have motion
      self.image = None

      # Found motion returned
      self.found_motion = False

      # Last frame analyzed
      self.__last_frame_number = 0

      # performance statistics
      self.__stat_number_of_frames = 0
      self.__stat_accumulated_time = 0

      QtCore.QThread.__init__(self)
      self.setObjectName("Analyzer-" + self.video.cam + "-QThread")

   def do_processing(self, image_cv, processing_frame_number):
      self.__image_cv = image_cv
      self.__processing_frame_number = processing_frame_number
      self.start()

   def run(self):
      self.analyze(self.video.cam)
    
   @timer("Time to analyze", logging.INFO, identifier='cam', average=1000)
   def analyze(self, cam):
      # We do not want to analyze the same frame twice
      if self.__processing_frame_number == self.__last_frame_number:
         return

      # Check to see if we are lagging behind
      if self.__last_frame_number + 1 != self.__processing_frame_number:
         logger.warning("Missed frame on camera " + self.video.cam + ": " + str(self.__processing_frame_number))
      self.__last_frame_number = self.__processing_frame_number

      start = time.time()

      image_gray_cv = self.__image_cv
      image_blur_cv = cv.GaussianBlur(image_gray_cv, (13, 13), 0)
      found_motion = False

      if self.__comparison_image_cv is not None:

         frame_delta = cv.absdiff(self.__comparison_image_cv, image_blur_cv)
         threshold = cv.threshold(frame_delta, 2, 255, cv.THRESH_BINARY)[1]
         threshold = cv.dilate(threshold, None, iterations=3)
         (self.__motion_boxes[self.__processing_frame_number], _) = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
#            print len(self.__motion_boxes[self.current_frame_number])

         #DEBUG  MOTION TRACK
#            if len(self.__motion_boxes[self.current_frame_number]) > 30:
         if False:
            if (self.video.direction == 0):
               found_motion = True
               self.video.direction = 90 * 6
         else:
            for c in self.__motion_boxes[self.__processing_frame_number]:
               found_motion = False
               (x, y, w, h) = cv.boundingRect(c)

               # Set ground level
               if y > self.video.groundlevel:
                  continue

               if cv.contourArea(c) < 15:
                  continue
               if cv.contourArea(c) > 10000:
                  continue
               if x < 160 and x + w > 160:
                  found_motion = True

               cv.rectangle(image_gray_cv, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 0, 0), 2)

               if found_motion and self.__processing_frame_number > 4 and self.video.direction == 0:
                  # Check previous motion boxes
                  direction = self.__check_overlap_previous(x, y, w, h, x, w, self.__processing_frame_number - 1, 10)

                  self.video.direction = direction * 90 * 6
#                     if self.video.direction != 0:
#                        print self.video.direction

                  if (self.video.direction != 0):
                     found_motion = True
                     break
                  else:
                     found_motion = False
               else:
                  found_motion = False

      self.__comparison_image_cv = image_blur_cv
      self.image = image_gray_cv
      self.found_motion_frame_number = self.__processing_frame_number
      self.found_motion = found_motion

      # statistics logging
      self.__stat_accumulated_time += (time.time() - start)
      self.__stat_number_of_frames += 1
      if self.__stat_number_of_frames % 1000 == 0:
         import threading
         thread = threading.Thread()
         thread.name="abc"
         logger.info("Time to analyze " + self.video.cam + ": " + str(int(self.__stat_accumulated_time / self.__stat_number_of_frames * 1000000)/1000) + "ms")
         self.__stat_accumulated_time = 0
         self.__stat_number_of_frames = 0

   def __check_overlap_previous(self, x, y, w, h, x1, w1, frame_number, iterations):
#      print "check overlap: " + str(frame_number) + " iteration: " + str(iterations)
      if not frame_number in self.__motion_boxes:
         return 0
      for c2 in self.__motion_boxes[frame_number]:
         (x2, y2, w2, h2) = cv.boundingRect(c2)

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
         return self.__check_overlap_previous(x2, y2, w2, h2, x1, w1, frame_number - 1, iterations -1)
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
   