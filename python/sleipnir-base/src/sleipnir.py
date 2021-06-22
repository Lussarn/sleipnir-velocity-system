import sys
import time

from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox
import cv2 as cv

from SleipnirWindow import SleipnirWindow
from Video import Video
from CamerasData import CamerasData
from Configuration import Configuration, ConfigurationError
from database.DB import DB
from Announcements import Announcements, Announcement
import database.announcement_dao as announcement_dao
from Frame import Frame
from CameraServer import CameraServer
from Globals import Globals
from AlignLogic import AlignLogic
from VideoPlayer import VideoPlayer
from Sound import Sound
from function_timer import timer

import logging
import logger

logger = logging.getLogger(__name__)

import Event

class WindowMain(QMainWindow):
   def __init__(self):
      QMainWindow.__init__(self)
      # Bootstrap event system
      Event.create_event_server(self)

      self.__db = None
      self.videos = {}  # type: dict[int, Video]

      try:
         self.configuration = Configuration("sleipnir.yml")
      except IOError as e:
         raise ConfigurationError("Unable to open configuration file sleipnir.yml")

      try:
         self.configuration.check_configuration()
      except ConfigurationError as e:
         raise e

      self.__db = DB(self.configuration.get_save_path())
      self.__max_dive_angle = self.configuration.get_max_dive_angle()
      logger.info("Max dive angle is set at " + str(self.__max_dive_angle) + "°")
      self.__blur_strength = self.configuration.get_blur_strength()
      logger.info("Blur strength is set at t at " + str(self.__blur_strength))

      # Data for the cameras
      self.__flight = 1
      self.cameras_data = CamerasData(self.__db, self.__flight)

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

      # Sound effects
      self.__sound = Sound()

      self.ui = SleipnirWindow()
      self.ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity - Go Fast!")

      self.ui.label_video1_online.setText("Cam1: Offline")
      self.ui.label_video2_online.setText("Cam2: Offline")

      self.announcements = Announcements()
      self.model_announcements = QtGui.QStandardItemModel()
      self.ui.listView_anouncements.setModel(self.model_announcements)
      self.__update_announcements_gui()



      # Init the videos
      self.videos['cam1'] = Video(
         self.__db,
         "cam1",
         1,
         self.__max_dive_angle,
         self.__blur_strength,
         self.ui.label_video1,  
         self.ui.label_time_video1)
      self.videos['cam2'] = Video(
         self.__db,
         "cam2",
         1,
         self.__max_dive_angle,
         self.__blur_strength,
         self.ui.label_video2, 
         self.ui.label_time_video2)

      # Start camera server
      self.__camera_server = CameraServer()
      self.__camera_server.start_server(self.__db)
      Event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_camera_online)
      Event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camera_offline)


      self.ui.label_speed.setText("")

      # Start / Stop connects
      self.ui.pushbutton_start.clicked.connect(self.cb_start_cameras)
      self.ui.pushbutton_stop.clicked.connect(self.stopCameras)

      # distance connect
      self.ui.lineEdit_distance.setText(str(self.distance))
      self.ui.lineEdit_distance.textChanged.connect(self.__cb_distance_changed)

      self.ui.listView_anouncements.clicked.connect(self.__cb_announcement_changed)
      self.ui.pushButton_remove_announcement.clicked.connect(self.__cb_remove_announcement_clicked)

      self.__globals = Globals(self.__db)
      self.__align_logic = AlignLogic(self.__globals, self.__camera_server)
      self.__video_player = VideoPlayer(self.__globals, self, self.configuration)

      ''' flight callbacks and events '''
      for radio_buttons_flight in self.ui.radio_buttons_flights:
         radio_buttons_flight.clicked.connect(self.__cb_flight)
      Event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

      ''' ground level callbacks and events '''
      self.ui.verticalSlider_groundlevel.valueChanged.connect(self.__cb_groundlevel_changed)
      Event.on(Globals.EVENT_GROUND_LEVEL_CHANGE, self.__evt_globals_ground_level_change)

      ''' Align callbacks and events '''
      self.ui.pushButton_video1_align.clicked.connect(self.__cb_align_cam1_clicked)
      self.ui.pushButton_video2_align.clicked.connect(self.__cb_align_cam2_clicked)
      Event.on(AlignLogic.EVENT_ALIGN_START, self.__evt_alignlogic_align_start)
      Event.on(AlignLogic.EVENT_ALIGN_STOP, self.__evt_alignlogic_align_stop)
      Event.on(AlignLogic.EVENT_ALIGN_NEW_FRAME, self.__evt_alignlogic_align_new_frame)
      self.ui.pushButton_video1_align.setEnabled(False)
      self.ui.pushButton_video2_align.setEnabled(False)

      ''' Video player callbacs and events '''
      Event.on(VideoPlayer.EVENT_FRAME_NEW, self.__evt_videoplayer_play_new_frame)

      ''' video 1 '''
      self.ui.pushbutton_video1_playforward.clicked.connect(self.__cb_video1_play_forward_clicked)
      self.ui.pushbutton_video1_playbackward.clicked.connect(self.__cb_video1_play_reverse_clicked)
      self.ui.pushbutton_video1_pause.clicked.connect(self.__cb_video1_stop_clicked)
      self.ui.pushbutton_video1_forwardstep.clicked.connect(self.__cb_video1_step_forward)
      self.ui.pushbutton_video1_backstep.clicked.connect(self.__cb_video1_step_reverse)
      self.ui.slider_video['cam1'].setMinimum(1)
      self.ui.slider_video['cam1'].valueChanged.connect(self.__cb_video1_slider_changed)
      self.ui.pushbutton_video1_copy.clicked.connect(self.__cb_video1_copy_clicked)
      self.ui.pushbutton_video1_find.clicked.connect(self.__cb_video1_find_clicked)

      ''' video 2 '''
      self.ui.pushbutton_video2_playforward.clicked.connect(self.__cb_video2_play_forward_clicked)
      self.ui.pushbutton_video2_playbackward.clicked.connect(self.__cb_video2_play_reverse_clicked)
      self.ui.pushbutton_video2_pause.clicked.connect(self.__cb_video2_stop_clicked)
      self.ui.pushbutton_video2_forwardstep.clicked.connect(self.__cb_video2_step_forward)
      self.ui.pushbutton_video2_backstep.clicked.connect(self.__cb_video2_step_reverse)
      self.ui.slider_video['cam2'].setMinimum(1)
      self.ui.slider_video['cam2'].valueChanged.connect(self.__cb_video2_slider_changed)
      self.ui.pushbutton_video2_copy.clicked.connect(self.__cb_video2_copy_clicked)
      self.ui.pushbutton_video2_find.clicked.connect(self.__cb_video2_find_clicked)

      ''' load flight number 1 '''
      self.__load_flight(1)


      # Show GUI
      self.show()
      self.raise_()

      # Run Gui
      self.timer = QtCore.QTimer(self)
      self.timer.timeout.connect(self.__timerGui)
      self.timer.start(20)

   '''
   Camera online GUI
   '''
   def __evt_camera_online(self, cam):
      if (cam == 'cam1'):
         self.ui.label_video1_online.setText("Cam1: Online")
         self.ui.pushButton_video1_align.setEnabled(True)
      else:
         self.ui.pushButton_video2_align.setEnabled(True)
         self.ui.label_video1_online.setText("Cam2: Online")

   def __evt_camera_offline(self, cam):
      if (cam == 'cam1'):
         self.ui.label_video1_online.setText("Cam1: Offline")
         self.ui.pushButton_video1_align.setEnabled(False)
      else:
         self.ui.label_video1_online.setText("Cam2: Offine")
         self.ui.pushButton_video2_align.setEnabled(False)

   '''
   Video player GUI
   '''
   def __cb_video1_play_forward_clicked(self): self.__video_play_forward_clicked('cam1')
   def __cb_video2_play_forward_clicked(self): self.__video_play_forward_clicked('cam2')
   def __video_play_forward_clicked(self, cam: str):
      self.__video_player.play(cam, VideoPlayer.DIRECTION_FORWARD)

   def __cb_video1_play_reverse_clicked(self): self.__video_play_reverse_clicked('cam1')
   def __cb_video2_play_reverse_clicked(self): self.__video_play_reverse_clicked('cam2')
   def __video_play_reverse_clicked(self, cam: str):
      self.__video_player.play(cam, VideoPlayer.DIRECTION_REVERSE)

   def __cb_video1_stop_clicked(self): self.__video_stop_clicked('cam1')
   def __cb_video2_stop_clicked(self): self.__video_stop_clicked('cam2')
   def __video_stop_clicked(self, cam: str):
      self.__video_player.stop(cam)

   def __cb_video1_step_forward(self): self.__video_step_forward('cam1')
   def __cb_video2_step_forward(self): self.__video_step_forward('cam2')
   def __video_step_forward(self, cam):
      self.__video_player.step(cam, VideoPlayer.DIRECTION_FORWARD)

   def __cb_video1_step_reverse(self): self.__video_step_reverse('cam1')
   def __cb_video2_step_reverse(self): self.__video_step_reverse('cam2')
   def __video_step_reverse(self, cam):
      self.__video_player.step(cam, VideoPlayer.DIRECTION_REVERSE)

   def __cb_video1_slider_changed(self, value): self.__video_slider_changed('cam1', value)
   def __cb_video2_slider_changed(self, value): self.__video_slider_changed('cam2', value)
   def __video_slider_changed(self, cam: str, value: int):
      self.__video_player.set_position(cam, value)

   def __cb_video1_copy_clicked(self): self.__video_copy('cam1', 'cam2')
   def __cb_video2_copy_clicked(self): self.__video_copy('cam2', 'cam1')
   def __video_copy(self, source_cam: str, dest_cam: str):
      self.__video_player.copy(source_cam, dest_cam)

   def __cb_video1_find_clicked(self): self.__video_find_clicked('cam1')
   def __cb_video2_find_clicked(self): self.__video_find_clicked('cam2')
   def __video_find_clicked(self, cam):
      self.__video_player.find(cam)

   def __evt_videoplayer_play_new_frame(self, frame :Frame):
      self.display_frame(frame)
      ''' block signal on slider change since it will do a video_player.set_poistion on change
      and thereby intrduce a circular event '''
      self.ui.slider_video[frame.get_cam()].blockSignals(True)
      self.ui.slider_video[frame.get_cam()].setSliderPosition(frame.get_position())
      self.ui.slider_video[frame.get_cam()].blockSignals(False)

      ''' Display time '''
      self.ui.label_time_video[frame.get_cam()].setText(
         self.__format_video_time(
            self.__video_player.get_time(frame.get_cam())
         )
      )

   def __format_video_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)

   def __enable_video_ui(self, enabled: bool):
      self.ui.pushbutton_video1_find.setEnabled(enabled)
      self.ui.pushbutton_video1_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video1_backstep.setEnabled(enabled)
      self.ui.pushbutton_video1_pause.setEnabled(enabled)
      self.ui.pushbutton_video1_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video1_playforward.setEnabled(enabled)
      self.ui.pushbutton_video1_copy.setEnabled(enabled)
      self.ui.pushbutton_video2_find.setEnabled(enabled)
      self.ui.pushbutton_video2_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video2_backstep.setEnabled(enabled)
      self.ui.pushbutton_video2_pause.setEnabled(enabled)
      self.ui.pushbutton_video2_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video2_playforward.setEnabled(enabled)
      self.ui.pushbutton_video2_copy.setEnabled(enabled)

   '''
   Align GUI
   '''
   def __cb_align_cam1_clicked(self):
      if self.ui.pushButton_video1_align.text() == 'Align Camera':
         self.__align_logic.start_align_camera('cam1')
      else:
         self.__align_logic.stop_align_camera('cam1')

   def __cb_align_cam2_clicked(self):
      if self.ui.pushButton_video2_align.text() == 'Align Camera':
         self.__align_logic.start_align_camera('cam2')
      else:
         self.__align_logic.stop_align_camera('cam2')

   def __evt_alignlogic_align_start(self, cam):
      self.enable_all_gui_elements(False)
      if cam == 'cam1':
         self.ui.pushButton_video1_align.setText('Stop')
         self.ui.pushButton_video2_align.setEnabled(False)
      else:
         self.ui.pushButton_video2_align.setText('Stop')
         self.ui.pushButton_video1_align.setEnabled(False)

   def __evt_alignlogic_align_stop(self, cam):
      self.enable_all_gui_elements(True)

      self.ui.pushButton_video1_align.setText('Align Camera')
      self.ui.pushButton_video2_align.setText('Align Camera')
      
      if self.__camera_server.is_online('cam1'): 
         self.ui.pushButton_video1_align.setEnabled(True)
      if self.__camera_server.is_online('cam2'): 
         self.ui.pushButton_video2_align.setEnabled(True)

   def __evt_alignlogic_align_new_frame(self, frame :Frame):
      self.display_frame(frame)

   '''
   Flight GUI
   '''
   def __cb_flight(self):
      for i in range(0,20):
         if self.ui.radio_buttons_flights[i].isChecked(): break
      self.__globals.set_flight(i + 1)

   def __evt_globals_flight_change(self, flight):
      self.ui.radio_buttons_flights[flight - 1].setChecked(True)
      self.__load_flight(flight)


   def __load_flight(self, flight):
      self.__flight = flight
      self.cameras_data = CamerasData(self.__db, self.__flight)
      self.ui.radio_buttons_flights[self.__flight - 1].setChecked(True)

      self.cameras_data.load(self.__db, self.__flight)
      self.__load_announcements(self.__flight)
      self.__update_announcements_gui()

      # FIXME: Clean this shit up to some kind of API
      self.videos['cam1'].cameras_data = self.cameras_data
      self.videos['cam2'].cameras_data = self.cameras_data
      self.videos['cam1'].set_flight(self.__flight)
      self.videos['cam2'].set_flight(self.__flight)
      self.ui.slider_video['cam1'].setMaximum(1 if not self.__video_player.get_last_frame("cam1") else (self.__video_player.get_last_frame('cam1').get_position() or 1))
      self.ui.slider_video['cam2'].setMaximum(1 if not self.__video_player.get_last_frame("cam2") else (self.__video_player.get_last_frame('cam2').get_position() or 1))
      self.__video_player.set_position('cam1', 1)
      self.__video_player.set_position('cam2', 1)
      self.videos['cam1'].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos['cam2'].setStartTimestamp(self.cameras_data.get_start_timestamp())
      self.videos['cam1'].comparison_image_cv = None
      self.videos['cam2'].comparison_image_cv = None
      
      self.videos['cam1'].view_frame(1)
      self.videos['cam2'].view_frame(1)


   def __cb_distance_changed(self, value):
      try:
         value = int(value)
      except:
         value = 100
      self.distance = value

   ''' ground level GUI '''
   def __cb_groundlevel_changed(self, value):
      self.__globals.set_ground_level(value)

   def __evt_globals_ground_level_change(self, value):
      ''' When the ground level change the videos needs to redraw '''
      self.display_frame(self.__video_player.get_current_frame('cam1'))
      self.display_frame(self.__video_player.get_current_frame('cam2'))

      self.videos['cam1'].groundlevel = value
      self.videos['cam2'].groundlevel = value

      ''' Do not try to set position if we are currently dragging '''
      if self.ui.verticalSlider_groundlevel.isSliderDown() == False:
         self.ui.verticalSlider_groundlevel.setValue(value)

   ''' display video frame '''
   def display_frame(self, frame :Frame):
      image = frame.get_image_load_if_missing(self.__db)

      # Draw center line
      cv.rectangle(image, (160, 0), (160, 480), (0, 0, 0), 1)
      # Draw ground level
      cv.rectangle(image, (0, self.__globals.get_ground_level()), (320, self.__globals.get_ground_level()), (0, 0, 0), 1)

      image_qt = QtGui.QImage(image, image.shape[1], image.shape[0], image.strides[0], QtGui.QImage.Format_Indexed8)
      self.ui.widget_video[frame.get_cam()].setPixmap(QtGui.QPixmap.fromImage(image_qt))


   @timer("Time to run gui", logging.INFO, None, average=1000)
   def __timerGui(self):
      online = self.__camera_server.is_online("cam1") and self.__camera_server.is_online("cam2")

      if (self.__shooting and not online):
         # Camera lost?
         self.__shooting = False
         self.__camera_server.stop_shooting()

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
         self.ui.pushbutton_stop.setText("Waiting...")
         self.ui.pushbutton_stop.setEnabled(False)
         if not self.__camera_server.is_shooting():
            self.stop_camera_wait = False
            self.__shooting = False
            self.ui.pushbutton_stop.setText("Stop cameras")
            self.ui.pushbutton_start.setEnabled(True)
            self.videos['cam1'].view_frame(1)
            self.videos['cam2'].view_frame(1)
            self.__enable_video_ui(True)
            self.timer.start(20)
            self.enable_all_gui_elements(True)

      # Update the video view
      if self.__camera_server.is_shooting():
         if self.__shooting:
            ''' Motion Track '''
            if self.ui.checkBox_motion_track.isChecked():
               for i in range(2):
                  cam = 'cam' + str(i+1)
                  video = self.videos[cam]
                  video.setStartTimestamp(self.cameras_data.get_start_timestamp())
                  if not video.is_analyzer_running():
                     last_frame = self.cameras_data.get_last_frame(cam)
                     if last_frame is not None:
                        frame_to_motion_check = self.get_frame_allow_lag(cam, last_frame.get_position())
                        if frame_to_motion_check is not None:
                           motion = video.view_frame_motion_track(
                              frame_to_motion_check.get_position(),
                              self.ui.checkBox_live.isChecked())                  
                           if motion is not None:
                              self.check_run(cam, motion)
                        else:
                           logger.warning("Frame to motioncheck is None on camera " +cam)
                     else:
                        logger.warning("Last frame is None on camera " +cam)

            else:
               ''' No motion track '''
               for i in range(2):
                  cam = 'cam' + str(i+1)
                  self.videos[cam].setStartTimestamp(self.cameras_data.get_start_timestamp())
                  if self.ui.checkBox_live.isChecked():
                     last_frame = self.cameras_data.get_last_frame(cam)
                     if last_frame is not None:
                        self.videos[cam].view_frame(last_frame.get_position())

         if self.run_direction is not None and self.run_abort_timestamp < int(round(time.time() * 1000)):
            # Abort run
            logger.info("Aborting run due to timeout")
            self.run_direction = None
            self.__sound.play_error()

         if self.run_tell_speed != 0 and self.run_tell_speed_timestamp < int(round(time.time() * 1000)):
            self.__sound.play_number(self.run_tell_speed)
            self.run_tell_speed = 0

      if self.cameras_data \
               and not self.__shooting \
               and (self.cameras_data.get_frame_count('cam1') or 0) >= 90 \
               and (self.cameras_data.get_frame_count('cam2') or 0) >= 90:
         # Calculate the speed
         cam1_frame_number = self.videos['cam1'].get_current_frame_number()
         cam2_frame_number = self.videos['cam2'].get_current_frame_number()
         self.set_speed(cam1_frame_number, cam2_frame_number)

   __last_served_frame = {
      'cam1': 0,
      'cam2': 0
   }
   def get_frame_allow_lag(self, cam: str, position: int) -> Frame:
      # Served frame can be larger than position if we stop and start camera, detect this
      # and reset served frame
      if position == 0: return None
      if self.__last_served_frame[cam] > position: self.__last_served_frame[cam] = 0
      if self.__last_served_frame[cam] < position - 30:
         # lag detected, jump
         self.__last_served_frame[cam] = position
         logger.warning("Lag detected when motion tracking " + cam + ": " + str(position))
      else:
         # Clamp __last_served_frame to position
         self.__last_served_frame[cam] = min(self.__last_served_frame[cam] + 1, position) 
      return self.cameras_data.get_frame(cam, self.__last_served_frame[cam])

   def set_speed(self, cam1_position, cam2_position):
      """
      Set speed from camera frame numbers
      """
      cam1_timestamp = self.cameras_data.get_frame('cam1', cam1_position).get_timestamp()
      cam2_timestamp = self.cameras_data.get_frame('cam2', cam2_position).get_timestamp()
      milliseconds = abs((cam1_timestamp or 0)- (cam2_timestamp or 0))

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


   def cb_start_cameras(self):
      logger.info("Starting Cameras")
      if not self.__camera_server.is_ready_to_shoot():
         return False

      for i in range(0,20):
         if self.ui.radio_buttons_flights[i].isChecked():
            break
      self.__flight = i + 1

      self.enable_all_gui_elements(False)

      self.announcements.clear()
      self.__update_announcements_gui()

      self.shooting_frame_number_cam1 = 1
      self.shooting_frame_number_cam2 = 1
      self.timer.start(10)

      self.ui.label_speed.setText("")
      self.stop_camera_wait = False
      self.__shooting = True
      self.videos['cam1'].reset()
      self.videos['cam2'].reset()
      self.__enable_video_ui(False)

      self.cameras_data = CamerasData(self.__db, self.__flight)
      self.videos['cam1'].cameras_data = self.cameras_data
      self.videos['cam2'].cameras_data = self.cameras_data
      self.__camera_server.start_shooting(self.__flight, self.cameras_data)


   def stopCameras(self):
      logger.info("Stoping Cameras")
      self.stop_camera_wait = True
      self.__camera_server.stop_shooting()
      self.__save_announcements()

   def enable_all_gui_elements(self, enabled):
      self.ui.pushbutton_video1_playforward.setEnabled(enabled)
      self.ui.pushbutton_video1_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video1_pause.setEnabled(enabled)
      self.ui.pushbutton_video1_find.setEnabled(enabled) 
      self.ui.pushbutton_video1_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video1_backstep.setEnabled(enabled)
      self.ui.slider_video1.setEnabled(enabled)
      self.ui.pushbutton_video1_copy.setEnabled(enabled)

      self.ui.pushbutton_video2_playforward.setEnabled(enabled)
      self.ui.pushbutton_video2_playbackward.setEnabled(enabled)
      self.ui.pushbutton_video2_pause.setEnabled(enabled)
      self.ui.pushbutton_video2_find.setEnabled(enabled) 
      self.ui.pushbutton_video2_forwardstep.setEnabled(enabled)
      self.ui.pushbutton_video2_backstep.setEnabled(enabled)
      self.ui.slider_video2.setEnabled(enabled)
      self.ui.pushbutton_video2_copy.setEnabled(enabled)

      self.ui.pushbutton_stop.setEnabled(enabled)
      self.ui.pushbutton_start.setEnabled(enabled)
      self.ui.checkBox_motion_track.setEnabled(enabled)
      self.ui.listView_anouncements.setEnabled(enabled)
      self.ui.verticalSlider_groundlevel.setEnabled(enabled)

      self.ui.pushButton_remove_announcement.setEnabled(enabled)


      for i in range(0, len(self.ui.radio_buttons_flights)):
         self.ui.radio_buttons_flights[i].setEnabled(enabled)

   def check_run(self, cam, motion):
      """
      Checking the motion tracking
      """
      if cam == "cam1" and self.run_direction == None and motion["direction"] == -1:
         # Camera 1 triggered LEFT run without being on a timed run. Reset the camera
         self.videos['cam1'].currently_tracking = 0
         logger.info("Camera 1 triggered the wrong way for start of run, reseting")
      if cam == "cam2" and self.run_direction == None and motion["direction"] == 1:
         # Camera 1 triggered RIGHT run without being on a timed run. Reset the camera
         self.videos['cam2'].currently_tracking = 0
         logger.info("Camera 2 triggered the wrong way for start of run, reseting")
      if cam == "cam1" and self.run_direction == 'LEFT' and motion["direction"] == 1:
         # Camera 1 triggered LEFT run without being on a timed run. Reset the camera
         self.videos['cam1'].currently_tracking = 0
         logger.info("Camera 1 triggered the wrong way in run, reseting")
      if cam == "cam2" and self.run_direction == 'RIGHT' and motion["direction"] == -1:
         # Camera 1 triggered RIGHT run without being on a timed run. Reset the camera
         self.videos['cam2'].currently_tracking = 0
         logger.info("Camera 2 triggered the wrong way in run, reseting")

      # Check right run
      if cam == "cam1" and self.run_direction == None and motion["direction"] == 1:
         # Starting run from cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_frame_number_cam2 = 0
         self.run_direction = "RIGHT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         self.__sound.play_gate_1()
         logger.info("Initiating time run from cam 1 -->")

      if cam == "cam2" and self.run_direction == "RIGHT" and motion["direction"] == 1:
         # Ending run on Cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         logger.info("Timed run completed on cam 2 -->")
         self.__sound.play_gate_2()
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
            logger.info("Adding announcement --> " + str(kmh) + " km/h")
            self.add_announcement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, 1)
         else:
            logger.warning("Do not add announcement over 500 km/h")
      

      # Check left run
      if cam == "cam2" and self.run_direction == None and motion["direction"] == -1:
         # Starting run from cam 2
         self.run_frame_number_cam2 = motion["frame_number"]
         self.run_frame_number_cam1 = 0
         self.run_direction = "LEFT"
         # Max 6 second run
         self.run_abort_timestamp = int(round(time.time() * 1000)) + 6000
         self.__sound.play_gate_1()
         logger.info("Initiating time run from cam 2 <--")

      if cam == "cam1" and self.run_direction == "LEFT" and motion["direction"] == -1:
         # Ending run on Cam 1
         self.run_frame_number_cam1 = motion["frame_number"]
         self.run_direction = None
         kmh = self.set_speed(self.run_frame_number_cam1, self.run_frame_number_cam2)
         self.__sound.play_gate_2()
         logger.info("Timed run completed on cam 2 <--")
         if (kmh < 500):
            self.run_tell_speed_timestamp = int(round(time.time() * 1000)) + 1000
            self.run_tell_speed = kmh
            self.add_announcement(self.run_frame_number_cam1, self.run_frame_number_cam2, kmh, -1)
            logger.info("Adding announcement <-- " + str(kmh) + " km/h")
         else:
            logger.warning("Do not add announcement over 500 km/h")

   def __cb_announcement_changed(self, event):
      self.__video_player.stop_all()
      self.__video_player.set_position('cam1', self.announcements.get_announcement_by_index(event.row()).get_cam1_position())
      self.__video_player.set_position('cam2', self.announcements.get_announcement_by_index(event.row()).get_cam2_position())

   def __cb_remove_announcement_clicked(self, event):
      index = self.ui.listView_anouncements.currentIndex().row()
      if index == -1:
         QMessageBox.information(self, 'Sleipnir Information', 'Select announcement to delete')
         return
      ret = QMessageBox.question(self, 'Sleipnir Information', "Confirm removing announcement", QMessageBox.Ok | QMessageBox.Cancel)
      if ret == QMessageBox.Cancel: return
      self.announcements.remove_announcement_by_index(index)
      self.__update_announcements_gui()

   def add_announcement(self, cam1_frame_number, cam2_frame_number, speed, direction):
      cam1_timestamp = self.cameras_data.get_frame("cam1", cam1_frame_number).get_timestamp()
      cam2_timestamp = self.cameras_data.get_frame("cam2", cam2_frame_number).get_timestamp()
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
      max_left = 0
      max_right = 0
      for announcement in self.announcements.get_announcements():
         out = ("--> " if (announcement.get_direction() == 1) else "<-- ") + \
            "%.3f" % (float(announcement.get_duration()) / 1000) + "s " + \
            str(announcement.get_speed()) + " km/h "
         self.model_announcements.appendRow(QtGui.QStandardItem(out))
         if announcement.get_direction() == 1: max_right = max(max_right, announcement.get_speed())
         if announcement.get_direction() == -1: max_left = max(max_left, announcement.get_speed())

      average = (max_left + max_right) / 2 if max_left > 0 and max_right > 0 else 0
      self.ui.label_average.setText("Average: " + "%.1f" % average + " km/h")


   def __save_announcements(self):
      logger.info("Saving announcements")
      announcement_dao.store(self.__db, self.__flight, self.announcements)

   def __load_announcements(self, flight):
      logger.info("Loading announcements")
      self.announcements = announcement_dao.fetch(self.__db, flight)

   def __del__(self):
      logger.debug("Mainwindow destructor called")
      if self.__db is not None:
         self.__db.stop()


if __name__ == '__main__':
   import sys
   app = QApplication(sys.argv)
   try:
      window = WindowMain()
      ret = app.exec_()
      del window
      sys.exit(ret)
   except ConfigurationError as e:
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Critical)
      msg_box.setWindowTitle("Sleipnir message")
      msg_box.setText("Configuration Error\n\n" + str(e))
      msg_box.exec_()
   except Exception:
      import traceback
      var = traceback.format_exc()
      msg_box = QMessageBox()
      msg_box.setIcon(QMessageBox.Critical)
      msg_box.setWindowTitle("Sleipnir message")
      msg_box.setText("UNRECOVERABLE ERROR!\n\n" + var)
      msg_box.exec_()
