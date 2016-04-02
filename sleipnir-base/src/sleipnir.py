import PySide
from PySide import QtCore, QtGui
import os
import datetime
import time
import pygame
import ConfigParser

import CameraServer
from Video import Video

from qtui.Ui_MainWindow import Ui_MainWindow

import CamerasData
import CameraServer

pygame.mixer.init()

class Anouncement:

   def __init__(self):
      self.cam1_frame_number = 0
      self.cam2_frame_number = 0
      self.time = 0
      self.speed = 0
      self.direction = 0

class WindowMain(QtGui.QMainWindow):

   def __init__(self):
      self.config = ConfigParser.ConfigParser()
      if not self.read_config():
         exit(0)

      CameraServer.ServerData.cameras_directory_base = self.cameras_directory_base

      self.cameras_data = None
      self.cameras_data = CamerasData.CamerasData()

      self.videos = {}
      self.radio_buttons_flights = {}

      # none / "Left" / "Right"
      self.run_direction = None
      self.run_frame_number_cam1 = None
      self.run_frame_number_cam2 = None
      # time to abort run
      self.run_abort_timestamp = 0 

      self.online_cam1 = False
      self.online_cam2 = False
      self.online = False
      self.ready = False
      self.shooting = False
      self.shooting_frame_number_cam1 = 0
      self.shooting_frame_number_cam2 = 0
      self.stop_camera_wait = False
      self.distance = 100

      self.run_tell_speed_timestamp = 0
      self.run_tell_speed = 0

      self.aligning_cam1 = False
      self.aligning_cam2 = False


      QtGui.QMainWindow.__init__(self)
      self.ui = Ui_MainWindow()
      self.ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity")

      self.anouncements = []
      self.model_anouncements = QtGui.QStandardItemModel(self.ui.listView_anouncements)
      self.update_anouncements()

      self.ui.label_video1_online.setText("Cam1: Offline")
      self.ui.label_video2_online.setText("Cam2: Offline")

      self.ui.verticalSlider_groundlevel.sliderMoved.connect(self.__on_groundlevel_changed)

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
         os.path.join(self.cameras_directory_base, "1", "cam1"), 
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
         os.path.join(self.cameras_directory_base, "1", "cam2"),
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

      self.ui.listView_anouncements.clicked.connect(self.__on_anouncement_changed)

      self.show()
      self.raise_()
      CameraServer.start_server()

      self.timer = QtCore.QTimer(self)
      self.timer.timeout.connect(self.__timerGui)
      self.timer.start(20)

   def load_flight(self, flight_number):
      self.radio_buttons_flights[flight_number - 1].setChecked(True)

      filename = os.path.join(self.cameras_directory_base, str(flight_number), "anouncements.csv")
      self.anouncements = []
      if self.cameras_data.load(self.cameras_directory_base, flight_number):
         if os.path.exists(filename):
            with open(filename, 'r') as f:
               for row in f:
                  row = row.split()
                  anouncement = Anouncement()
                  anouncement.cam1_frame_number = int(row[0])
                  anouncement.cam2_frame_number = int(row[1])
                  anouncement.time = int(row[2])
                  anouncement.speed = int(row[3])
                  anouncement.direction = int(row[4])
                  self.anouncements.append(anouncement)
      self.update_anouncements()


      # FIXME: Clean this shit up to some kind of API
      self.videos[0].cameras_data = self.cameras_data
      self.videos[1].cameras_data = self.cameras_data
      self.videos[0].flight_directory = os.path.join(self.cameras_directory_base, str(flight_number), "cam1")
      self.videos[1].flight_directory = os.path.join(self.cameras_directory_base, str(flight_number), "cam2")
      self.videos[0].slider.setMinimum(1)
      self.videos[0].slider.setMaximum(self.cameras_data.get_last_frame("cam1"))
      self.videos[1].slider.setMinimum(1)
      self.videos[1].slider.setMaximum(self.cameras_data.get_last_frame("cam2"))
      self.videos[0].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[1].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[0].set_current_frame_number(1)
      self.videos[1].set_current_frame_number(1)
      self.videos[0].comparison_image_cv = None
      self.videos[1].comparison_image_cv = None
      self.videos[0].found_motion = False
      self.videos[1].found_motion = False
      
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

   def __on_groundlevel_changed(self, value):
      self.videos[0].groundlevel = value
      self.videos[1].groundlevel = value

   def __on_anouncement_changed(self, event):
      row = event.row()
      anouncement = self.anouncements[row]
      self.videos[0].set_current_frame_number(anouncement.cam1_frame_number)
      self.videos[1].set_current_frame_number(anouncement.cam2_frame_number)

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
               self.timer.start(20)

      # Update the video view
      if CameraServer.is_shooting():
         if self.aligning_cam1:
            frame_number = CameraServer.get_last_image("cam1")
            if frame_number > 0:
               self.videos[0].view_frame(frame_number)
         elif self.aligning_cam2:
            frame_number = CameraServer.get_last_image("cam2")
            if frame_number > 0:
               self.videos[1].view_frame(frame_number)
         else:
            if self.ui.checkBox_motion_track.isChecked():
               if self.shooting_frame_number_cam1 <= CameraServer.get_last_image("cam1"):
                  start = CameraServer.get_start_timestamp()
                  self.videos[0].setStartTimestamp(start)
                  motion = self.videos[0].view_frame_motion_track(CameraServer.get_last_image("cam1"))
                  if motion is not None:
                     self.check_run("cam1", motion)
                     print "motion cam1: " + str(motion)
                  self.shooting_frame_number_cam1 += 1
               if self.shooting_frame_number_cam2 <= CameraServer.get_last_image("cam2"):
                  start = CameraServer.get_start_timestamp()
                  self.videos[1].setStartTimestamp(start)
                  motion = self.videos[1].view_frame_motion_track(CameraServer.get_last_image("cam2"))
                  if motion is not None:
                     self.check_run("cam2", motion)
                     print "motion cam2: " + str(motion)
                  self.shooting_frame_number_cam2 += 1
            else:
               if self.shooting_frame_number_cam1 <= CameraServer.get_last_image("cam1"):
                  start = CameraServer.get_start_timestamp()
                  self.videos[0].setStartTimestamp(start)
                  self.videos[0].view_frame(CameraServer.get_last_image("cam1"))
                  self.shooting_frame_number_cam1 += 1
               if self.shooting_frame_number_cam2 <= CameraServer.get_last_image("cam2"):
                  start = CameraServer.get_start_timestamp()
                  self.videos[1].setStartTimestamp(start)
                  self.videos[1].view_frame(CameraServer.get_last_image("cam2"))
                  self.shooting_frame_number_cam2 += 1

         if self.run_direction is not None and self.run_abort_timestamp < int(round(time.time() * 1000)):
            # Abort run
            self.run_direction = None
            source = pygame.mixer.Sound("../assets/sounds/error.ogg")
            source.play()

         if self.run_tell_speed != 0 and self.run_tell_speed_timestamp < int(round(time.time() * 1000)):
            source = pygame.mixer.Sound("../assets/sounds/numbers/" + str(self.run_tell_speed) + ".ogg")
            source.play()
            self.run_tell_speed = 0


      if self.cameras_data and not self.shooting and self.cameras_data.is_data_ok() and not self.aligning_cam1 and not self.aligning_cam2:
         # Calculate the speed
         cam1_frame_number = self.videos[0].get_current_frame_number()
         cam2_frame_number = self.videos[1].get_current_frame_number()
         self.set_speed(cam1_frame_number, cam2_frame_number)

   def set_speed(self, cam1_frame_number, cam2_frame_number):
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
      return int(kmh)

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

      self.anouncements = []
      self.update_anouncements()

      self.shooting_frame_number_cam1 = 1
      self.shooting_frame_number_cam2 = 1
      self.timer.start(0)

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
      self.save_anouncements()

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
      self.ui.checkBox_motion_track.setEnabled(enabled)
      self.ui.listView_anouncements.setEnabled(enabled)
      self.ui.verticalSlider_groundlevel.setEnabled(enabled)

      for i in xrange(0,20):
         self.radio_buttons_flights[i].setEnabled(enabled)

   def check_run(self, cam, motion):
      # Check right run
      if cam == "cam1" and self.run_direction == None and motion["direction"] == 1:
         # Starting run from cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_frame_number_cam2 = 0
         self.run_direction = "RIGHT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         print "STARTING RUN CAM1"
         source = pygame.mixer.Sound("../assets/sounds/gate-1.ogg")
         source.play()

      if cam == "cam2" and self.run_direction == "RIGHT" and motion["direction"] == 1:
         # Ending run on Cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         print "ENDING RUN CAM2"
         source = pygame.mixer.Sound("../assets/sounds/gate-2.ogg")
         source.play()
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
         self.add_anouncement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, 1)

      # Check left run
      if cam == "cam2" and self.run_direction == None and motion["direction"] == -1:
         # Starting run from cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_frame_number_cam1 = 0
         self.run_direction = "LEFT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         print "STARTING RUN CAM2"
         source = pygame.mixer.Sound("../assets/sounds/gate-1.ogg")
         source.play()


      if cam == "cam1" and self.run_direction == "LEFT" and motion["direction"] == -1:
         # Ending run on Cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         print "ENDING RUN CAM1"
         source = pygame.mixer.Sound("../assets/sounds/gate-2.ogg")
         source.play()
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
         self.add_anouncement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, -1)

   def add_anouncement(self, cam1_frame_number, cam2_frame_number, kmh, direction):
      cam1_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam1", cam1_frame_number)
      cam2_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam2", cam2_frame_number)
      milliseconds = abs(cam1_timestamp - cam2_timestamp)
      anouncement = Anouncement()
      anouncement.cam1_frame_number = cam1_frame_number
      anouncement.cam2_frame_number = cam2_frame_number
      anouncement.time = milliseconds
      anouncement.speed = kmh
      anouncement.direction = direction
      self.anouncements.append(anouncement)
      self.update_anouncements()

   def update_anouncements(self):
      self.model_anouncements.clear()

      for anouncement in self.anouncements:
         out = ""
         if (anouncement.direction == 1):
            out += "--> "
         else:
            out += "<-- "

         out += "%.3f" % (float(anouncement.time) / 1000) + "s "
         out += str(anouncement.speed) + "Kmh "
         item = QtGui.QStandardItem()
         item.setText(out)
         self.model_anouncements.appendRow(item)

      self.ui.listView_anouncements.setModel(self.model_anouncements)

   def save_anouncements(self):
      for flight_number in xrange(0,20):
         if self.radio_buttons_flights[flight_number].isChecked():
            break
      flight_number += 1
      filename = os.path.join(self.cameras_directory_base, str(flight_number), "anouncements.csv")

      with open(filename, 'w') as f:
         for anouncement in self.anouncements:
            out = str(anouncement.cam1_frame_number) + "  " + str(anouncement.cam2_frame_number) + " "
            out += str(anouncement.time) + " "
            out += str(anouncement.speed) + " "
            out += str(anouncement.direction) + "\n"
            f.write(out)

   def read_config(self):
      filename = self.get_config_filename()
      if self.config.read(filename) == None:
         print "No config file: " + filename
         return False
      self.cameras_directory_base = self.config.get("Files", "save_path")
      return True


   def get_config_filename(self):
      if sys.platform.startswith("win32"):
         from win32com.shell import shell,shellcon
         home = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
      else:
         home = os.path.expanduser("~")
      return os.path.join(home, "sleipnir.cfg")

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
