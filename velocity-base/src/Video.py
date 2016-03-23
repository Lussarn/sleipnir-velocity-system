import PySide
from PySide import QtCore, QtGui
from PIL import Image, ImageDraw
import os
import cv2 as cv
import numpy

class Video:

   def __init__(self, cam, camdir, widgetVideo, buttonPlayForward, buttonPlayBackward, buttonPause, buttonFind, buttonForwardStep, buttonBackStep, slider, buttonCopy, labelTime):

      self.current_frame_number = 0
      self.find = False
      self.comparisonCV = None
      self.staticFrameCount = 0
      self.foundMotion = False
      self.shooting = False
      self.forward = True

      self.cam = cam

      self.camdir = camdir
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

      self.timer = QtCore.QTimer(self.widgetVideo)
      self.timer.timeout.connect(self.__timerplay)

      self.current_frame_number = 0
      find = False
      comparisonCV = None
      staticFrameCount = 0
      foundMotion = False
      self.start_timestamp = 0


   def set_sibling_video(self, sibling_video):
      self.sibling_video = sibling_video

   def reset(self):
      self.current_frame_number = 1
      self.find = False
      self.comparisonCV = None
      self.staticFrameCount = 0 
      self.foundMotion = 0

   def set_shooting(self, shooting):
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

   def get_current_frame_number(self):
      return self.current_frame_number

   def set_current_frame_number(self, frame_number):
      self.current_frame_number = frame_number
      self.update()

   def getFrame(self, frame):
      file = self.camdir + "/" + str((frame / 100) *100).zfill(6)
      if not os.path.exists(file):
         return None

      timestamp = self.cameras_data.get_timestamp_from_frame_number(self.cam, frame)

      imageFileName = self.camdir + "/" + str((frame / 100) *100).zfill(6) + "/image" + str(frame).zfill(9) + ".jpg"
      pilImage = Image.open(imageFileName);
      return { "timestamp": int(timestamp), "image": pilImage }

   def setStartTimestamp(self, start_timestamp):
      self.start_timestamp = start_timestamp


   def __onCopy(self):
      timestamp_this = self.cameras_data.get_timestamp_from_frame_number(self.cam, self.current_frame_number)

      for i in range(1, self.cameras_data.get_last_frame(self.sibling_video.cam) + 1):
         timestamp_sibling = self.cameras_data.get_timestamp_from_frame_number(self.sibling_video.cam, i)
         if timestamp_sibling >= timestamp_this:
            break

      self.sibling_video.set_current_frame_number(i)


   def __onSliderChanged(self, value):
      self.current_frame_number = value
      self.update()
      self.timer.stop()

   def __onPlayForward(self):
      self.find = False
      self.forward = True
      self.timer.start(11)

   def __onPlayBackward(self):
      self.find = False
      self.forward = False
      self.timer.start(11)

   def __onPause(self):
      self.timer.stop()
      self.update()

   def __onFind(self):
      self.find = True
      self.timer.start(1)

   def __onForwardStep(self):
      if self.current_frame_number < self.cameras_data.get_last_frame(self.cam):
         self.current_frame_number += 1
      self.timer.stop()
      self.update()

   def __onBackStep(self):
      if self.current_frame_number > 1:
         self.current_frame_number -= 1
      self.timer.stop()
      self.update()

   def __timerplay(self):
      if self.find:
         frame = self.getFrame(self.current_frame_number)
         if not frame:
            return
         imagePil = frame["image"];

         imageCV = self.pilImageToCV(imagePil)
         grayCV = cv.cvtColor(imageCV, cv.COLOR_BGR2GRAY)
         blurCV = cv.GaussianBlur(grayCV, (21, 21), 0)

         if self.foundMotion == False and (self.staticFrameCount == 0 or self.staticFrameCount > 15):
            self.comparisonCV = blurCV
            self.staticFrameCount = 1

         frameDelta = cv.absdiff(self.comparisonCV, blurCV)
         thresh = cv.threshold(frameDelta, 2, 255, cv.THRESH_BINARY)[1]
         thresh = cv.dilate(thresh, None, iterations=2)
         (cnts, _) = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

         if (self.foundMotion == False):
            for c in cnts:
               if cv.contourArea(c) < 100:
                  continue
               if cv.contourArea(c) > 10000:
                  continue
               (x, y, w, h) = cv.boundingRect(c)
               self.timer.stop()
               self.staticFrameCount = 1
               self.foundMotion = True
         else:
            stillMotion = False
            for c in cnts:
               if cv.contourArea(c) > 100:
                  stillMotion = True
                  (x, y, w, h) = cv.boundingRect(c)
                  cv.rectangle(grayCV, (x, y), (x + w, y + h), (0, 255, 0), 2)
                  break
            if stillMotion == False:
               self.staticFrameCount = 1
               self.foundMotion = False

      self.staticFrameCount += 1
      if self.forward:
         self.current_frame_number += 1
         if self.current_frame_number > self.cameras_data.get_last_frame(self.cam):
            self.current_frame_number = self.cameras_data.get_last_frame(self.cam)   
      else:
         self.current_frame_number -= 1
         if (self.current_frame_number < 1):
            self.current_frame_number  =1
      self.update()

   def view_image(self, image):
      self.current_frame_number = image
      self.update()

   def update(self):
      frame = self.getFrame(self.current_frame_number)
      if not frame:
         return

      if (self.shooting):
         self.slider.setSliderPosition(1)
      else:
         self.slider.setSliderPosition(self.current_frame_number)

      local_timestamp = frame["timestamp"] - self.start_timestamp
      if (local_timestamp < 0):
         local_timestamp = 0
      self.labelTime.setText(self.__format_time(local_timestamp))

      imagePil = frame["image"];
      draw = ImageDraw.Draw(imagePil)
      draw.line((imagePil.width / 2, 0, imagePil.width / 2, imagePil.height), fill=0)
      del draw

      pilData = self.pilToBytes(imagePil.convert("RGBA"),'raw','BGRA')
      imageQ = QtGui.QImage(pilData, imagePil.size[0], imagePil.size[1], QtGui.QImage.Format_ARGB32)
      pixmapQ = QtGui.QPixmap.fromImage(imageQ)

      pixmapQscaled = pixmapQ.scaled(480, 720, QtCore.Qt.KeepAspectRatio)
      self.widgetVideo.setPixmap(pixmapQscaled)

   def pilToBytes(self, image, encoder_name='raw', *args):
      try:
         return image.tobytes(encoder_name, args)
      except:
         pass
      return image.tostring(encoder_name, args)

   def pilImageToCV(self, imagePil):
      imageCV = numpy.array(imagePil.convert("RGB")) 
      imageCV = imageCV[:, :, ::-1].copy()
      return imageCV   

   def cvImageToPil(self, imageCV, conversion):
      imageCV = cv.cvtColor(imageCV, conversion)
      return Image.fromarray(imageCV)

   def __format_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)
