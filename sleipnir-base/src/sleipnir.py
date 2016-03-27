import PySide
from PySide import QtCore, QtGui
import os
import datetime
import time

import CameraServer
from Video import Video

from qtui.Ui_MainWindow import Ui_MainWindow

import CamerasData
import CameraServer

class WindowMain(QtGui.QMainWindow):

   def __init__(self):
      self.cameras_directory_base = "/home/linus/rctest/"
      CameraServer.ServerData.camdir = self.cameras_directory_base


      self.cameras_data = None
      self.cameras_data = CamerasData.CamerasData()

      self.videos = {}

      self.radio_buttons_flights = {}

      self.online_cam1 = False
      self.online_cam2 = False
      self.online = False
      self.ready = False
      self.shooting = False
      self.stop_camera_wait = False
      self.distance = 100

      self.aligning_cam1 = False
      self.aligning_cam2 = False

      QtGui.QMainWindow.__init__(self)
      self.ui = Ui_MainWindow()
      self.ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity")

      self.ui.label_video1_online.setText("Cam1: Offline")
      self.ui.label_video2_online.setText("Cam2: Offline")

      self.radio_buttons_flights[0] = self.ui.radioButton_flight_1
      self.radio_buttons_flights[1] = self.ui.radioButton_flight_2
      self.radio_buttons_flights[2] = self.ui.radioButton_flight_3
      self.radio_buttons_flights[3] = self.ui.radioButton_flight_4
      self.radio_buttons_flights[4] = self.ui.radioButton_flight_5
      self.radio_buttons_flights[5] = self.ui.radioButton_flight_6
      self.radio_buttons_flights[6] = self.ui.radioButton_flight_7
      self.radio_buttons_flights[7] = self.ui.radioButton_flight_8
      self.radio_buttons_flights[8] = self.ui.radioButton_flight_9
      self.radio_buttons_flights[9] = self.ui.radioButton_flight_10
      self.radio_buttons_flights[10] = self.ui.radioButton_flight_11
      self.radio_buttons_flights[11] = self.ui.radioButton_flight_12
      self.radio_buttons_flights[12] = self.ui.radioButton_flight_13
      self.radio_buttons_flights[13] = self.ui.radioButton_flight_14
      self.radio_buttons_flights[14] = self.ui.radioButton_flight_15
      self.radio_buttons_flights[15] = self.ui.radioButton_flight_16
      self.radio_buttons_flights[16] = self.ui.radioButton_flight_17
      self.radio_buttons_flights[17] = self.ui.radioButton_flight_18
      self.radio_buttons_flights[18] = self.ui.radioButton_flight_19
      self.radio_buttons_flights[19] = self.ui.radioButton_flight_20
      for i in xrange(0,20):
         self.radio_buttons_flights[i].clicked.connect(self.__flight_number_clicked)

      self.videos[0] = Video(
         "cam1",
         "/home/linus/rctest/3/cam1", 
         self.ui.label_video1, 
         self.ui.pushbutton_video1_playforward, 
         self.ui.pushbutton_video1_playbackward, 
         self.ui.pushbutton_video1_pause, 
         self.ui.pushbutton_video1_find, 
         self.ui.pushbutton_video1_forwardstep, 
         self.ui.pushbutton_video1_backstep,
         self.ui.slider_video1,
         self.ui.pushbutton_video1_copy,
         self.ui.label_time_video1);
      self.videos[1] = Video(
         "cam2",
         "/home/linus/rctest/3/cam2",
         self.ui.label_video2, 
         self.ui.pushbutton_video2_playforward, 
         self.ui.pushbutton_video2_playbackward, 
         self.ui.pushbutton_video2_pause, 
         self.ui.pushbutton_video2_find, 
         self.ui.pushbutton_video2_forwardstep, 
         self.ui.pushbutton_video2_backstep, 
         self.ui.slider_video2,
         self.ui.pushbutton_video2_copy,
         self.ui.label_time_video2);
      self.videos[0].set_sibling_video(self.videos[1])
      self.videos[1].set_sibling_video(self.videos[0])

      self.load_flight(1)

      self.ui.label_speed.setText("")

      self.ui.pushbutton_start.clicked.connect(self.startCameras)
      self.ui.pushbutton_stop.clicked.connect(self.stopCameras)

      self.ui.pushButton_video1_align.clicked.connect(self.align_cam1)
      self.ui.pushButton_video2_align.clicked.connect(self.align_cam2)

      self.ui.lineEdit_distance.setText(str(self.distance))
      self.ui.lineEdit_distance.textChanged.connect(self.__on_distance_changed)

      self.show()
      self.raise_()
      CameraServer.start_server()

      self.timer = QtCore.QTimer(self)
      self.timer.timeout.connect(self.__timerGui)
      self.timer.start(20)

   def load_flight(self, flight_number):
      self.radio_buttons_flights[flight_number - 1].setChecked(True)

      self.cameras_data.load(self.cameras_directory_base, flight_number)
      self.videos[0].cameras_data = self.cameras_data
      self.videos[1].cameras_data = self.cameras_data
      self.videos[0].camdir = os.path.join(self.cameras_directory_base, str(flight_number), "cam1")
      self.videos[1].camdir = os.path.join(self.cameras_directory_base, str(flight_number), "cam2")
      self.videos[0].slider.setMinimum(1)
      self.videos[0].slider.setMaximum(self.cameras_data.get_last_frame("cam1"))
      self.videos[1].slider.setMinimum(1)
      self.videos[1].slider.setMaximum(self.cameras_data.get_last_frame("cam2"))
      self.videos[0].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[1].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[0].set_current_frame_number(1)
      self.videos[1].set_current_frame_number(1)
      self.videos[0].update();
      self.videos[1].update();

   def __flight_number_clicked(self):
      for i in xrange(0,20):
         if self.radio_buttons_flights[i].isChecked():
            break
      self.load_flight(i + 1)

   def __on_distance_changed(self, value):
      try:
         value = int(value)
      except:
         value = 100
      self.distance = value


   def __timerGui(self):
      self.online_cam1 = CameraServer.is_online("cam1")
      self.online_cam2 = CameraServer.is_online("cam2")
      self.online = CameraServer.is_online("cam1") and CameraServer.is_online("cam2")

      if self.online_cam1:
         self.ui.label_video1_online.setText("Cam1: Online")
         if not self.aligning_cam2 and not self.shooting:
           self.ui.pushButton_video1_align.setEnabled(True)
      if self.online_cam2:
         self.ui.label_video2_online.setText("Cam2: Online")
         if not self.aligning_cam1 and not self.shooting:
            self.ui.pushButton_video2_align.setEnabled(True)

      if not self.online_cam1:
         self.ui.label_video1_online.setText("Cam1: Offline")
         self.ui.pushButton_video1_align.setEnabled(False)
      if not self.online_cam2:
         self.ui.label_video2_online.setText("Cam2: Offline")
         self.ui.pushButton_video2_align.setEnabled(False)

      self.ready = CameraServer.is_ready();
      
      if (self.shooting and not self.online):
         # Camera lost?
         self.shooting = False;
         CameraServer.stop_shooting()


      if not self.online:
         self.ui.pushbutton_start.setEnabled(False)
         self.ui.pushbutton_stop.setEnabled(False)

      if self.ready and self.online:
         self.ui.pushbutton_start.setEnabled(True)
         self.ui.pushbutton_stop.setEnabled(False)

      if self.shooting and self.online:
         self.ui.pushbutton_start.setEnabled(False)
         self.ui.pushbutton_stop.setEnabled(True)

      if (self.stop_camera_wait):
         if self.aligning_cam1:
            self.ui.pushButton_video1_align.setEnabled(False)
            if not CameraServer.is_shooting():
               self.aligning_cam1 = False
               self.ui.pushButton_video1_align.setEnabled(True)
               self.stop_camera_wait = False
               self.videos[0].set_shooting(False)
               self.ui.pushButton_video1_align.setText("Align Camera")
         elif self.aligning_cam2:
            self.ui.pushButton_video2_align.setEnabled(False)
            if not CameraServer.is_shooting():
               self.aligning_cam2 = False
               self.ui.pushButton_video2_align.setEnabled(True)
               self.stop_camera_wait = False
               self.videos[1].set_shooting(False)
               self.ui.pushButton_video2_align.setText("Align Camera")
         else:
            self.ui.pushbutton_stop.setText("Waiting...")
            self.ui.pushbutton_stop.setEnabled(False)
            if not CameraServer.is_shooting():
               self.stop_camera_wait = False
               self.shooting = False
               self.ui.pushbutton_stop.setText("Stop cameras")
               self.ui.pushbutton_start.setEnabled(True)
               self.videos[0].set_current_frame_number(1)
               self.videos[1].set_current_frame_number(1)
               self.videos[0].set_shooting(False)
               self.videos[1].set_shooting(False)

      # Update the video view
      if CameraServer.is_shooting():
         if self.aligning_cam1:
            frame_number = CameraServer.get_last_image("cam1")
            if frame_number > 0:
               self.videos[0].view_image(frame_number)
         elif self.aligning_cam2:
            frame_number = CameraServer.get_last_image("cam2")
            if frame_number > 0:
               self.videos[1].view_image(frame_number)
         else:
            start = CameraServer.get_start_timestamp()
            frame_number = CameraServer.get_last_image("cam1")
            if frame_number > 0:
               self.videos[0].setStartTimestamp(start)
               self.videos[0].view_image(frame_number)

            frame_number = CameraServer.get_last_image("cam2")
            if frame_number > 0:
               self.videos[1].setStartTimestamp(start)
               self.videos[1].view_image(frame_number)

      if self.cameras_data and not self.shooting and self.cameras_data.is_data_ok() and not self.aligning_cam1 and not self.aligning_cam2:
         # Calculate the speed
         cam1_frame_number = self.videos[0].get_current_frame_number()
         cam2_frame_number = self.videos[1].get_current_frame_number()

         cam1_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam1", cam1_frame_number)
         cam2_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam2", cam2_frame_number)
         milliseconds = abs(cam1_timestamp - cam2_timestamp)

         kilometer = float(self.distance) / 1000
         hours = float(milliseconds) / 1000 / 60  / 60

         if (hours > 0):
            kmh = kilometer / hours
         else:
            kmh = 0
         if (kmh > 999 or kmh  < 10):
            speed_text = "Out of range"
            time_text = "Out of range"
         else:
            speed_text = '{1:.{0}f} km/h'.format(1, kmh)
            time_text = '{1:.{0}f} sec'.format(3, float(milliseconds) / 1000)

         self.ui.label_speed.setText(speed_text)
         self.ui.label_time.setText(time_text)

   def align_cam1(self):
      if (self.aligning_cam1):
         self.stop_camera_wait = True
         CameraServer.stop_shooting()         
      else:
         self.aligning_cam1 = True
         self.videos[0].set_shooting(True)
         self.cameras_data = CamerasData.CamerasData()
         self.videos[0].cameras_data = self.cameras_data
         CameraServer.start_shooting(self.cameras_data, 1)
         self.enable_all_gui_elements(False)
         self.ui.pushButton_video1_align.setText("Stop")

   def align_cam2(self):
      if (self.aligning_cam2):
         self.stop_camera_wait = True
         CameraServer.stop_shooting()         
      else:
         self.aligning_cam2 = True
         self.videos[1].set_shooting(True)
         self.cameras_data = CamerasData.CamerasData()
         self.videos[1].cameras_data = self.cameras_data
         CameraServer.start_shooting(self.cameras_data, 1)
         self.enable_all_gui_elements(False)
         self.ui.pushButton_video2_align.setText("Stop")

   def startCameras(self):
      if not CameraServer.is_ready():
         return False

      for flight_number in xrange(0,20):
         if self.radio_buttons_flights[flight_number].isChecked():
            break
      flight_number += 1

      self.ui.label_speed.setText("")
      self.stop_camera_wait = False
      self.shooting = True
      self.videos[0].reset()
      self.videos[1].reset()
      self.videos[0].set_shooting(True)
      self.videos[1].set_shooting(True)
      self.cameras_data = CamerasData.CamerasData()
      self.videos[0].cameras_data = self.cameras_data
      self.videos[1].cameras_data = self.cameras_data
      CameraServer.ServerData.flight_number = flight_number
      CameraServer.ServerData.camera_directory_base = self.cameras_directory_base
      CameraServer.start_shooting(self.cameras_data, flight_number)
 
   def stopCameras(self):
      self.stop_camera_wait = True
      CameraServer.stop_shooting()

   def enable_all_gui_elements(self, enabled):
      self.ui.pushbutton_video1_playforward.setEnabled(enabled)
      self.ui.pushbutton_video1_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video1_pause.setEnabled(enabled)
      self.ui.pushbutton_video1_find.setEnabled(enabled) 
      self.ui.pushbutton_video1_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video1_backstep.setEnabled(enabled)
      self.ui.pushButton_video1_align.setEnabled(enabled)
      self.ui.slider_video1.setEnabled(enabled)
      self.ui.pushbutton_video1_copy.setEnabled(enabled)

      self.ui.pushbutton_video2_playforward.setEnabled(enabled)
      self.ui.pushbutton_video2_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video2_pause.setEnabled(enabled)
      self.ui.pushbutton_video2_find.setEnabled(enabled) 
      self.ui.pushbutton_video2_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video2_backstep.setEnabled(enabled)
      self.ui.pushButton_video2_align.setEnabled(enabled)
      self.ui.slider_video2.setEnabled(enabled)
      self.ui.pushbutton_video2_copy.setEnabled(enabled)

      self.ui.pushbutton_stop.setEnabled(enabled)
      self.ui.pushbutton_start.setEnabled(enabled)

      for i in xrange(0,20):
         self.radio_buttons_flights[i].setEnabled(enabled)


if __name__ == '__main__':
   import sys
   app = QtGui.QApplication(sys.argv)
   try:
      window = WindowMain()
      sys.exit(app.exec_())
   except Exception:
      import traceback
      var = traceback.format_exc()
      msg_box = QtGui.QMessageBox()
      msg_box.setIcon(QtGui.QMessageBox.Critical)
      msg_box.setWindowTitle("Sleipnir message")
      msg_box.setText("UNRECOVERABLE ERROR!\n\n" + var)
      msg_box.exec_()
