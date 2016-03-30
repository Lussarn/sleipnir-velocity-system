import PySide
from PySide import QtCore, QtGui
from PIL import Image, ImageDraw
import os
import cv2 as cv
import numpy

class Video:

   def __init__(self, cam, flight_directory, widgetVideo, buttonPlayForward, buttonPlayBackward, buttonPause, buttonFind, buttonForwardStep, buttonBackStep, slider, buttonCopy, labelTime):

      # Frame number in video
      self.current_frame_number = 0

      # Find flag
      self.find = False

      # Comparision for motion tracking
      self.comparison_image_cv = None

      # Currently found motion
      self.found_motion = 0

      # Motion direction
      self.direction = 0

      # Motion boxes for all frames
      self.motion_boxes = {}

      # Currently shooting
      self.shooting = False

      # Forward / Backward flag
      self.forward = True

      # cam1 or cam2
      self.cam = cam

      # Directory of flight
      self.flight_directory = flight_directory

      # Timestamp to start video on, this is the higest number of the two cameras
      self.start_timestamp = 0

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


   # Sibling video is the Video instance of the other camera
   def set_sibling_video(self, sibling_video):
      self.sibling_video = sibling_video

   # Reset parameters
   def reset(self):
      self.current_frame_number = 1
      self.find = False
      self.comparison_image_cv = None
      self.comparison_image_frame_count = 0 
      self.found_motion = 0
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

   # Sets current frame number of video
   def set_current_frame_number(self, frame_number):
      self.current_frame_number = frame_number
      self.update()

   # Returns a video frame as a pil image and it's timestamp
   def getFrame(self, frame_number):
      file = self.flight_directory + "/" + str((frame_number / 100) *100).zfill(6)
      if not os.path.exists(file):
         return None
      timestamp = self.cameras_data.get_timestamp_from_frame_number(self.cam, frame_number)
      picture_filename = self.flight_directory + "/" + str((frame_number / 100) *100).zfill(6) + "/image" + str(frame_number).zfill(9) + ".jpg"
      pil_image = Image.open(picture_filename);
      return { "timestamp": int(timestamp), "image": pil_image }

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
      self.sibling_video.set_current_frame_number(i)
      self.sibling_video.direction = 0

   def __onSliderChanged(self, value):
      self.direction = 0
      self.current_frame_number = value
      self.update()
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
      self.update()

   def __onFind(self):
      self.find = True
      self.found_motion = False
      self.forward = True
      self.timer.start(0)

   def __onForwardStep(self):
      self.direction = 0
      if self.current_frame_number < self.cameras_data.get_last_frame(self.cam):
         self.current_frame_number += 1
      self.timer.stop()
      self.update()

   def __onBackStep(self):
      self.direction = 0
      if self.current_frame_number > 1:
         self.current_frame_number -= 1
      self.timer.stop()
      self.update()

   def __timerplay(self):
      image = None

      if self.forward:
         self.current_frame_number += 1
         if self.current_frame_number > self.cameras_data.get_last_frame(self.cam):
            self.current_frame_number = self.cameras_data.get_last_frame(self.cam)   
      else:
         self.current_frame_number -= 1
         if (self.current_frame_number < 1):
            self.current_frame_number  =1

      frame = self.getFrame(self.current_frame_number)
      if not frame:
         return
      image_pil = frame["image"];

      if self.forward:
         motion = self.have_motion(image_pil)
         if self.find:
            image = motion["image"]
            if motion["motion"]:
               self.timer.stop()

      self.update(image)

   def have_motion(self, image_pil):
      image = None
      image_cv = self.pilImageToCV(image_pil)
      image_gray_cv = cv.cvtColor(image_cv, cv.COLOR_BGR2GRAY)
      image_blur_cv = cv.GaussianBlur(image_gray_cv, (11, 11), 0)
      found_motion = False

      if self.direction < 0:
         self.direction +=1

      if self.direction > 0:
         self.direction -=1

      if self.comparison_image_cv is not None:

         frame_delta = cv.absdiff(self.comparison_image_cv, image_blur_cv)
         threshold = cv.threshold(frame_delta, 2, 255, cv.THRESH_BINARY)[1]
         threshold = cv.dilate(threshold, None, iterations=3)
         (self.motion_boxes[self.current_frame_number], _) = cv.findContours(threshold.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

         for c in self.motion_boxes[self.current_frame_number]:
            found_motion = False
            (x, y, w, h) = cv.boundingRect(c)

            # Set ground level
            if y > 400:
               continue

            cv.rectangle(image_gray_cv, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 0, 0), 2)

            if cv.contourArea(c) < 15:
               continue
            if cv.contourArea(c) > 10000:
               continue
            if x < 160 and x + w > 160:
               found_motion = True

            if found_motion and self.current_frame_number > 4 and self.direction == 0:
               # Check previous motion boxes
               direction = self.check_overlap_previous(x, y, w, h, self.current_frame_number - 1, 5)

               self.direction = direction * 90 * 6
               print self.direction

               if (self.direction != 0):
                  found_motion = True
                  break
               else:
                  found_motion = False
            else:
               found_motion = False

         data_pil = cv.cvtColor(image_gray_cv, cv.COLOR_GRAY2BGR)
         image = Image.fromarray(data_pil)

      self.comparison_image_cv = image_blur_cv
      return { "motion": found_motion, "image": image }

   def check_overlap_previous(self, x, y, w, h, frame_number, iterations):
      print "check overlap: " + str(frame_number) + " iteration: " + str(iterations)
      for c2 in self.motion_boxes[frame_number]:
         (x2, y2, w2, h2) = cv.boundingRect(c2)

         if cv.contourArea(c2) < 15:
            continue
         if cv.contourArea(c2) > 10000:
            continue

         if x == x2 and y == y2 and w == w2 and h == h2 :
            continue

         # Sanity on size
         if w < 5 or h < 5 or w > 160 or h > 160:
            continue

         # the sizes of the boxes can't be too far off
         diff = float(w * h) / float(w2 * h2)
         if diff < 0.5 or diff > 1.5:
            continue

         direction =  self.overlap_box(x, y, w, h, x2, y2, w2, h2);
         if (direction == 0):
            continue
         else:
            if (iterations == 0):
               return direction
            return self.check_overlap_previous(x2, y2, w2, h2, frame_number - 1, iterations -1)
      return 0

   # Return 0 on non overlap
   def overlap_box(self, x, y, w, h, x2, y2, w2, h2):
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
         return -1;
      else:
         return 1   

   def view_image(self, frame_number):
      self.current_frame_number = frame_number
      self.update()

   def update(self, use_image = None):
      frame = self.getFrame(self.current_frame_number)
      if not frame:
         return

      local_timestamp = frame["timestamp"] - self.start_timestamp
      if (local_timestamp < 0):
         local_timestamp = 0
      self.labelTime.setText(self.__format_time(local_timestamp))

      if use_image:
         frame["image"] = use_image

      if (self.shooting):
         self.slider.setSliderPosition(1)
      else:
         self.slider.setSliderPosition(self.current_frame_number)

      image_pil = frame["image"];
      draw = ImageDraw.Draw(image_pil)
      draw.line((image_pil.width / 2, 0, image_pil.width / 2, image_pil.height), fill=0)
      del draw

      pilData = self.pilToBytes(image_pil.convert("RGBA"),'raw','BGRA')
      imageQ = QtGui.QImage(pilData, image_pil.size[0], image_pil.size[1], QtGui.QImage.Format_ARGB32)
      pixmapQ = QtGui.QPixmap.fromImage(imageQ)

      pixmapQscaled = pixmapQ.scaled(480, 720, QtCore.Qt.KeepAspectRatio)
      self.widgetVideo.setPixmap(pixmapQscaled)

   def pilToBytes(self, image, encoder_name='raw', *args):
      try:
         return image.tobytes(encoder_name, args)
      except:
         pass
      return image.tostring(encoder_name, args)

   def pilImageToCV(self, image_pil):
      image_cv = numpy.array(image_pil.convert("RGB")) 
      image_cv = image_cv[:, :, ::-1].copy()
      return image_cv   

   def cvImageToPil(self, image_cv, conversion):
      image_cv = cv.cvtColor(image_cv, conversion)
      return Image.fromarray(image_cv)

   def __format_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)
