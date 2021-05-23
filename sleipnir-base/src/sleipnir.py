import PySide2
from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox

import os
import datetime
import time
import configparser

from SleipnirWindow import SleipnirWindow
import util
import CameraServer
from Video import Video
import CamerasData
import CameraServer

import pyglet 
pyglet.options['audio'] = ('directsound', 'openal', 'pulse',  'silent')

class Announcement:
   def __init__(self,
      cam1_frame_number,
      cam2_frame_number,
      time,
      speed,
      direction):

      self.__cam1_frame_number = cam1_frame_number
      self.__cam2_frame_number = cam2_frame_number
      self.__time = time
      self.__speed = speed
      self.__direction = direction 

   def get_cam1_frame_number(self):
      return self.__cam1_frame_number

   def get_cam2_frame_number(self):
      return self.__cam2_frame_number

   def get_time(self):
      return self.__time

   def get_speed(self):
      return self.__speed

   def get_direction(self):
      return self.__direction

class Announcements:
   def __init__(self):
      self.__announcements = []

   def clear(self):
      self.__announcements = []

   def append(self, announcement: Announcement):
      self.__announcements.append(announcement)

   def get_announcement_by_index(self, index):
      return self.__announcements[index]

   def get_announcements(self):
      return self.__announcements

class WindowMain(QMainWindow):
   def __init__(self):
      # Init config
      self.config = configparser.ConfigParser()
      if not self.read_config():
         exit(0)

      # Set cameras_directory_base for the server
      CameraServer.ServerData.cameras_directory_base = self.cameras_directory_base

      # Data for the cameras
      self.cameras_data = CamerasData.CamerasData()

      # none / "Left" / "Right"
      self.run_direction = None
      self.run_frame_number_cam1 = None
      self.run_frame_number_cam2 = None
      # time to abort run
      self.run_abort_timestamp = 0 

      # Currently shooting
      self.__shooting = False

      # Frame number from shooting cameras
      self.shooting_frame_number_cam1 = 0
      self.shooting_frame_number_cam2 = 0

      # Waiting for cameras to stop
      self.stop_camera_wait = False

      # Distance
      self.distance = 100

      self.run_tell_speed_timestamp = 0
      self.run_tell_speed = 0

      # Aligning cameras 1/2
      self.aligning_cam1 = False
      self.aligning_cam2 = False

      # Sound effects
      self.sound_effects = { 
         "gate-1" : pyglet.media.StaticSource(pyglet.media.load(util.resource_path("sounds/gate-1.ogg"))),
         "gate-2" : pyglet.media.StaticSource(pyglet.media.load(util.resource_path("sounds/gate-2.ogg"))),
         "error"  : pyglet.media.StaticSource(pyglet.media.load(util.resource_path("sounds/error.ogg")))
      }

      QMainWindow.__init__(self)
      self.ui = SleipnirWindow()
      self.ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity - Go Fast!")

      self.ui.label_video1_online.setText("Cam1: Offline")
      self.ui.label_video2_online.setText("Cam2: Offline")

      self.announcements = Announcements()
      self.model_announcements = QtGui.QStandardItemModel()
      self.ui.listView_anouncements.setModel(self.model_announcements)
      self.__update_announcements_gui()

      self.ui.verticalSlider_groundlevel.sliderMoved.connect(self.__on_groundlevel_changed)

      for radio_buttons_flight in self.ui.radio_buttons_flights:
         radio_buttons_flight.clicked.connect(self.__flight_number_clicked)

      # [0] - left [1] - right video
      # Init the videos
      self.videos = {}
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
         self.ui.label_time_video1)
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
         self.ui.label_time_video2)
      self.videos[0].set_sibling_video(self.videos[1])
      self.videos[1].set_sibling_video(self.videos[0])

      # Load flight number 1
      self.load_flight(1)

      self.ui.label_speed.setText("")

      # Start / Stop connects
      self.ui.pushbutton_start.clicked.connect(self.startCameras)
      self.ui.pushbutton_stop.clicked.connect(self.stopCameras)

      # Align cameras connects
      self.ui.pushButton_video1_align.clicked.connect(self.align_cam1)
      self.ui.pushButton_video2_align.clicked.connect(self.align_cam2)

      # distance connect
      self.ui.lineEdit_distance.setText(str(self.distance))
      self.ui.lineEdit_distance.textChanged.connect(self.__on_distance_changed)

      self.ui.listView_anouncements.clicked.connect(self.__on_announcement_changed)

      # Show GUI
      self.show()
      self.raise_()

      # Start camera server
      CameraServer.start_server()

      # Run Gui
      self.timer = QtCore.QTimer(self)
      self.timer.timeout.connect(self.__timerGui)
      self.timer.start(20)

   def load_flight(self, flight_number):
      """
      Load a flight
      """
      self.ui.radio_buttons_flights[flight_number - 1].setChecked(True)

      filename = os.path.join(self.cameras_directory_base, str(flight_number), "announcements.csv")
      self.announcements.clear()
      if self.cameras_data.load(self.cameras_directory_base, flight_number):
         if os.path.exists(filename):
            with open(filename, 'r') as f:
               for row in f:
                  row = row.split()
                  self.announcements.append(Announcement(
                     int(row[0]),
                     int(row[1]),
                     int(row[2]),
                     int(row[3]),
                     int(row[4])
                  ))
      self.__update_announcements_gui()


      # FIXME: Clean this shit up to some kind of API
      self.videos[0].cameras_data = self.cameras_data
      self.videos[1].cameras_data = self.cameras_data
      self.videos[0].set_flight_directory(os.path.join(self.cameras_directory_base, str(flight_number), "cam1"))
      self.videos[1].set_flight_directory(os.path.join(self.cameras_directory_base, str(flight_number), "cam2"))
      self.videos[0].slider.setMinimum(1)
      self.videos[0].slider.setMaximum(self.cameras_data.get_last_frame("cam1"))
      self.videos[1].slider.setMinimum(1)
      self.videos[1].slider.setMaximum(self.cameras_data.get_last_frame("cam2"))
      self.videos[0].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[1].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos[0].comparison_image_cv = None
      self.videos[1].comparison_image_cv = None
      
      self.videos[0].view_frame(1)
      self.videos[1].view_frame(1)

   def __flight_number_clicked(self):
      for i in range(0,20):
         if self.ui.radio_buttons_flights[i].isChecked():
            break
      self.load_flight(i + 1)


   def __on_distance_changed(self, value):
      try:
         value = int(value)
      except:
         value = 100
      self.distance = value

   def __on_groundlevel_changed(self, value):
      # Forward ground level to videos
      self.videos[0].groundlevel = value
      self.videos[1].groundlevel = value
      self.videos[0].view_frame(self.videos[0].get_current_frame_number())
      self.videos[1].view_frame(self.videos[1].get_current_frame_number())

   def __on_announcement_changed(self, event):
      self.videos[0].view_frame(self.announcements.get_announcement_by_index(event.row()).get_cam1_frame_number())
      self.videos[1].view_frame(self.announcements.get_announcement_by_index(event.row()).get_cam2_frame_number())

   def __timerGui(self):
      pyglet.clock.tick()

      online = CameraServer.is_online("cam1") and CameraServer.is_online("cam2")

      if CameraServer.is_online("cam1"):
         self.ui.label_video1_online.setText("Cam1: Online")
         if not self.aligning_cam2 and not self.__shooting:
           self.ui.pushButton_video1_align.setEnabled(True)
      if CameraServer.is_online("cam2"):
         self.ui.label_video2_online.setText("Cam2: Online")
         if not self.aligning_cam1 and not self.__shooting:
            self.ui.pushButton_video2_align.setEnabled(True)

      if not  CameraServer.is_online("cam1"):
         self.ui.label_video1_online.setText("Cam1: Offline")
         self.ui.pushButton_video1_align.setEnabled(False)
      if not CameraServer.is_online("cam2"):
         self.ui.label_video2_online.setText("Cam2: Offline")
         self.ui.pushButton_video2_align.setEnabled(False)

      if (self.__shooting and not online):
         # Camera lost?
         self.__shooting = False
         CameraServer.stop_shooting()

      if not online:
         self.ui.pushbutton_start.setEnabled(False)
         self.ui.pushbutton_stop.setEnabled(False)
      elif self.__shooting:
         self.ui.pushbutton_start.setEnabled(False)
         self.ui.pushbutton_stop.setEnabled(True)
      else:
         self.ui.pushbutton_start.setEnabled(True)
         self.ui.pushbutton_stop.setEnabled(False)

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
            print("aligning 2 stop")
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
               self.__shooting = False
               self.ui.pushbutton_stop.setText("Stop cameras")
               self.ui.pushbutton_start.setEnabled(True)
               self.videos[0].view_frame(1)
               self.videos[1].view_frame(1)
               self.videos[0].set_shooting(False)
               self.videos[1].set_shooting(False)
               self.timer.start(20)
               self.enable_all_gui_elements(True)

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
                  motion = self.videos[0].view_frame_motion_track(CameraServer.get_next_image("cam1"), self.ui.checkBox_live.isChecked())
                  if motion is not None:
                     self.check_run("cam1", motion)
                  self.shooting_frame_number_cam1 += 1
               if self.shooting_frame_number_cam2 <= CameraServer.get_last_image("cam2"):
                  start = CameraServer.get_start_timestamp()
                  self.videos[1].setStartTimestamp(start)
                  motion = self.videos[1].view_frame_motion_track(CameraServer.get_next_image("cam2"), self.ui.checkBox_live.isChecked())
                  if motion is not None:
                     self.check_run("cam2", motion)
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
            self.sound_effects["error"].play()

         if self.run_tell_speed != 0 and self.run_tell_speed_timestamp < int(round(time.time() * 1000)):
            source= pyglet.media.StaticSource(pyglet.media.load(util.resource_path("sounds/numbers/" + str(self.run_tell_speed) + ".ogg")))
            source.play()
            self.run_tell_speed = 0


      if self.cameras_data and not self.__shooting and self.cameras_data.is_data_ok() and not self.aligning_cam1 and not self.aligning_cam2:
         # Calculate the speed
         cam1_frame_number = self.videos[0].get_current_frame_number()
         cam2_frame_number = self.videos[1].get_current_frame_number()
         self.set_speed(cam1_frame_number, cam2_frame_number)

   def set_speed(self, cam1_frame_number, cam2_frame_number):
      """
      Set speed from camera frame numbers
      """
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
      """
      Align camera one
      """
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
      """
      Align camera two
      """
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
      print("INFO: WindowMain.startCameras() Starting Cameras")
      if not CameraServer.is_ready_to_shoot():
         return False

      for flight_number in range(0,20):
         if self.ui.radio_buttons_flights[flight_number].isChecked():
            break
      flight_number += 1

      self.enable_all_gui_elements(False)

      self.announcements.clear()
      self.__update_announcements_gui()

      self.shooting_frame_number_cam1 = 1
      self.shooting_frame_number_cam2 = 1
      self.timer.start(6)

      self.ui.label_speed.setText("")
      self.stop_camera_wait = False
      self.__shooting = True
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
      print("INFO: WindowMain.stopCameras() Stoping Cameras")
      self.stop_camera_wait = True
      CameraServer.stop_shooting()
      self.save_announcements()

   def enable_all_gui_elements(self, enabled):
      """
      Enable or disable GUI elements
      """
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

      for i in range(0, len(self.ui.radio_buttons_flights)):
         self.ui.radio_buttons_flights[i].setEnabled(enabled)

   def check_run(self, cam, motion):
      """
      Checking the motion tracking
      """
      # Check right run
      if cam == "cam1" and self.run_direction == None and motion["direction"] == 1:
         # Starting run from cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_frame_number_cam2 = 0
         self.run_direction = "RIGHT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         self.sound_effects["gate-1"].play()

      if cam == "cam2" and self.run_direction == "RIGHT" and motion["direction"] == 1:
         # Ending run on Cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         self.sound_effects["gate-2"].play()
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
         self.add_announcement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, 1)

      # Check left run
      if cam == "cam2" and self.run_direction == None and motion["direction"] == -1:
         # Starting run from cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_frame_number_cam1 = 0
         self.run_direction = "LEFT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         self.sound_effects["gate-1"].play()


      if cam == "cam1" and self.run_direction == "LEFT" and motion["direction"] == -1:
         # Ending run on Cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         self.sound_effects["gate-2"].play()
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
         self.add_announcement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, -1)

   def add_announcement(self, cam1_frame_number, cam2_frame_number, speed, direction):
      cam1_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam1", cam1_frame_number)
      cam2_timestamp = self.cameras_data.get_timestamp_from_frame_number("cam2", cam2_frame_number)
      milliseconds = abs(cam1_timestamp - cam2_timestamp)

      self.announcements.append(Announcement(
         cam1_frame_number,
         cam2_frame_number,
         milliseconds,
         speed,
         direction
      ))
      self.__update_announcements_gui()

   def __update_announcements_gui(self):
      self.model_announcements.clear()
      for announcement in self.announcements.get_announcements():
         out = ("--> " if (announcement.get_direction() == 1) else "<-- ") + \
            "%.3f" % (float(announcement.get_time()) / 1000) + "s " + \
            str(announcement.get_speed()) + " km/h "
         self.model_announcements.appendRow(QtGui.QStandardItem(out))

   def save_announcements(self):
      for flight_number in range(0, len(self.ui.radio_buttons_flights)):
         if self.ui.radio_buttons_flights[flight_number].isChecked():
            break

      flight_number += 1
      filename = os.path.join(self.cameras_directory_base, str(flight_number), "announcements.csv")

      with open(filename, 'w') as f:
         for announcement in self.announcements.get_announcements():
            out = str(announcement.get_cam1_frame_number()) + "  " + str(announcement.get_cam2_frame_number()) + " "
            out += str(announcement.get_time()) + " "
            out += str(announcement.get_speed()) + " "
            out += str(announcement.get_direction()) + "\n"
            f.write(out)

   def read_config(self):
      filename = self.get_config_filename()
      print("Config file: " + filename)
      if self.config.read(filename) == None:
         print ("No config file: " + filename)
         return False

      print(self.config)   
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
   app = QApplication(sys.argv)
   try:
      window = WindowMain()
      sys.exit(app.exec_())
   except Exception:
      import traceback
      var = traceback.format_exc()
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Critical)
      msg_box.setWindowTitle("Sleipnir message")
      msg_box.setText("UNRECOVERABLE ERROR!\n\n" + var)
      msg_box.exec_()
