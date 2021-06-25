import sys
import time

from PySide2 import QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox
import cv2 as cv

from sleipnir_window import SleipnirWindow
from speed_logic import SpeedLogic, SpeedPassMessage
from configuration import Configuration, ConfigurationError
from database.db import DB
from announcements import Announcements, Announcement
from frame import Frame
from camera_server import CameraServer
from globals import Globals
from align_logic import AlignLogic
from video_player import VideoPlayer
from sound import Sound
from errors import *

import logging
import logger

logger = logging.getLogger(__name__)

import event

class WindowMain(QMainWindow):
   def __init__(self):
      QMainWindow.__init__(self)
      ''' Bootstrap event system '''
      event.create_event_server(self)

      try:
         self.__configuration = Configuration("sleipnir.yml")
      except IOError as e:
         raise ConfigurationError("Unable to open configuration file sleipnir.yml")

      try:
         self.__configuration.check_configuration()
      except ConfigurationError as e:
         raise e
      self.__db = DB(self.__configuration.get_save_path())

      ''' Setup Sound '''
      self.__sound = Sound()

      ''' Main window setup '''
      self.__ui = SleipnirWindow()
      self.__ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity - Go Fast!")

      ''' Start camera server '''
      self.__camera_server = CameraServer()
      self.__camera_server.start_server(self.__db)
      event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_cameraserver_camera_online)
      event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_cameraserver_camera_offline)
      self.__ui.label_video1_online.setText("Cam1: Offline")
      self.__ui.label_video2_online.setText("Cam2: Offline")

      ''' Initalize components '''
      self.__globals = Globals(self.__db)
      self.__video_player = VideoPlayer(self.__globals, self, self.__configuration)
      self.__align_logic = AlignLogic(self.__globals, self.__camera_server)
      self.__speed_logic = SpeedLogic(self.__globals, self.__camera_server, self.__configuration)

      ''' game callbacks and events '''
      event.on(Globals.EVENT_GAME_CHANGE, self.__evt_globals_game_change)
      self.__ui.combo_box_game_select.currentIndexChanged.connect(self.__cb_game_changed)

      ''' flight callbacks and events '''
      for radio_buttons_flight in self.__ui.radio_buttons_flights:
         radio_buttons_flight.clicked.connect(self.__cb_flight)
      event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

      ''' ground level callbacks and events '''
      self.__ui.verticalSlider_groundlevel.valueChanged.connect(self.__cb_groundlevel_changed)
      event.on(Globals.EVENT_GROUND_LEVEL_CHANGE, self.__evt_globals_ground_level_change)

      ''' Align callbacks and events '''
      self.__ui.pushButton_video1_align.clicked.connect(self.__cb_align_cam1_clicked)
      self.__ui.pushButton_video2_align.clicked.connect(self.__cb_align_cam2_clicked)
      event.on(AlignLogic.EVENT_ALIGN_START, self.__evt_alignlogic_align_start)
      event.on(AlignLogic.EVENT_ALIGN_STOP, self.__evt_alignlogic_align_stop)
      event.on(AlignLogic.EVENT_ALIGN_NEW_FRAME, self.__evt_alignlogic_align_new_frame)
      self.__ui.pushButton_video1_align.setEnabled(False)
      self.__ui.pushButton_video2_align.setEnabled(False)

      ''' Video player callbacs and events '''
      event.on(VideoPlayer.EVENT_FRAME_NEW, self.__evt_videoplayer_play_new_frame)

      ''' video 1 '''
      self.__ui.pushbutton_video1_playforward.clicked.connect(self.__cb_video1_play_forward_clicked)
      self.__ui.pushbutton_video1_playbackward.clicked.connect(self.__cb_video1_play_reverse_clicked)
      self.__ui.pushbutton_video1_pause.clicked.connect(self.__cb_video1_stop_clicked)
      self.__ui.pushbutton_video1_forwardstep.clicked.connect(self.__cb_video1_step_forward)
      self.__ui.pushbutton_video1_backstep.clicked.connect(self.__cb_video1_step_reverse)
      self.__ui.slider_video['cam1'].setMinimum(1)
      self.__ui.slider_video['cam1'].valueChanged.connect(self.__cb_video1_slider_changed)
      self.__ui.pushbutton_video1_copy.clicked.connect(self.__cb_video1_copy_clicked)
      self.__ui.pushbutton_video1_find.clicked.connect(self.__cb_video1_find_clicked)

      ''' video 2 '''
      self.__ui.pushbutton_video2_playforward.clicked.connect(self.__cb_video2_play_forward_clicked)
      self.__ui.pushbutton_video2_playbackward.clicked.connect(self.__cb_video2_play_reverse_clicked)
      self.__ui.pushbutton_video2_pause.clicked.connect(self.__cb_video2_stop_clicked)
      self.__ui.pushbutton_video2_forwardstep.clicked.connect(self.__cb_video2_step_forward)
      self.__ui.pushbutton_video2_backstep.clicked.connect(self.__cb_video2_step_reverse)
      self.__ui.slider_video['cam2'].setMinimum(1)
      self.__ui.slider_video['cam2'].valueChanged.connect(self.__cb_video2_slider_changed)
      self.__ui.pushbutton_video2_copy.clicked.connect(self.__cb_video2_copy_clicked)
      self.__ui.pushbutton_video2_find.clicked.connect(self.__cb_video2_find_clicked)

      ''' Speed callbacks and events '''
      self.__ui.pushbutton_start.clicked.connect(self.__cb_start_cameras)
      self.__ui.pushbutton_stop.clicked.connect(self.__cb_stop_cameras)
      event.on(SpeedLogic.EVENT_SPEED_START, self.__evt_speedlogic_speed_start)
      event.on(SpeedLogic.EVENT_SPEED_STOP, self.__evt_speedlogic_speed_stop)
      event.on(SpeedLogic.EVENT_SPEED_NEW_FRAME, self.__evt_speedlogic_speed_new_frame)
      event.on(SpeedLogic.EVENT_PASS_START, self.__evt_speedlogic_pass_start)
      event.on(SpeedLogic.EVENT_PASS_END, self.__evt_speedlogic_pass_end)
      event.on(SpeedLogic.EVENT_PASS_ABORT, self.__evt_speedlogic_pass_abort)
      self.__ui.pushbutton_stop.setEnabled(False)
      self.__ui.pushbutton_start.setEnabled(False)
      self.__ui.lineEdit_distance.setText(str(self.__speed_logic.get_distance()))
      self.__ui.lineEdit_distance.textChanged.connect(self.__cb_distance_changed)
      ''' Announcement '''
      event.on(SpeedLogic.EVENT_ANNOUNCEMENT_NEW, self.__evt_speedlogic_announcement_new)
      event.on(SpeedLogic.EVENT_ANNOUNCEMENT_LOAD, self.__evt_speedlogic_announcement_load)
      self.__ui.listView_anouncements.clicked.connect(self.__cb_speed_logic_announcement_changed)
      self.__ui.pushButton_remove_announcement.clicked.connect(self.__cb_remove_announcement_clicked)
      self.__speed_logic_model_announcements = QtGui.QStandardItemModel()
      self.__ui.listView_anouncements.setModel(self.__speed_logic_model_announcements)

      ''' load flight number 1 '''
      self.__globals.set_flight(1)

      ''' Show GUI '''
      self.show()
      self.raise_()

   def __del__(self):
      logger.debug("Mainwindow destructor called")
      if self.__db is not None:
         self.__db.stop()


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º    Camera Online GUI    ¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __evt_cameraserver_camera_online(self, cam):
      if (cam == 'cam1'):
         self.__ui.label_video1_online.setText("Cam1: Online")
         self.__ui.pushButton_video1_align.setEnabled(True)
      else:
         self.__ui.pushButton_video2_align.setEnabled(True)
         self.__ui.label_video1_online.setText("Cam2: Online")

      if self.__camera_server.is_ready_to_shoot():
         self.__ui.pushbutton_start.setEnabled(True)
         self.__ui.pushbutton_stop.setEnabled(False)
      
   def __evt_cameraserver_camera_offline(self, cam):
      if (cam == 'cam1'):
         self.__ui.label_video1_online.setText("Cam1: Offline")
         self.__ui.pushButton_video1_align.setEnabled(False)
      else:
         self.__ui.label_video1_online.setText("Cam2: Offine")
         self.__ui.pushButton_video2_align.setEnabled(False)

      self.__ui.pushbutton_start.setEnabled(False)
      self.__ui.pushbutton_stop.setEnabled(False)


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤    Video Player GUI    ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

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
      self.__ui.slider_video[frame.get_cam()].blockSignals(True)
      self.__ui.slider_video[frame.get_cam()].setSliderPosition(frame.get_position())
      self.__ui.slider_video[frame.get_cam()].blockSignals(False)

      ''' Display time '''
      self.__ui.label_time_video[frame.get_cam()].setText(
         self.__format_video_time(
            self.__video_player.get_time(frame.get_cam())
         )
      )

   def __format_video_time(self, ms):
      return "%02d:%02d:%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)

   def __enable_video_ui(self, enabled: bool):
      self.__ui.pushbutton_video1_find.setEnabled(enabled)
      self.__ui.pushbutton_video1_playbackward.setEnabled(enabled)
      self.__ui.pushbutton_video1_backstep.setEnabled(enabled)
      self.__ui.pushbutton_video1_pause.setEnabled(enabled)
      self.__ui.pushbutton_video1_forwardstep.setEnabled(enabled)
      self.__ui.pushbutton_video1_playforward.setEnabled(enabled)
      self.__ui.pushbutton_video1_copy.setEnabled(enabled)
      self.__ui.pushbutton_video2_find.setEnabled(enabled)
      self.__ui.pushbutton_video2_playbackward.setEnabled(enabled)
      self.__ui.pushbutton_video2_backstep.setEnabled(enabled)
      self.__ui.pushbutton_video2_pause.setEnabled(enabled)
      self.__ui.pushbutton_video2_forwardstep.setEnabled(enabled)
      self.__ui.pushbutton_video2_playforward.setEnabled(enabled)
      self.__ui.pushbutton_video2_copy.setEnabled(enabled)


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Align GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __cb_align_cam1_clicked(self):
      if self.__ui.pushButton_video1_align.text() == 'Align Camera':
         self.__align_logic.start_align_camera('cam1')
      else:
         self.__align_logic.stop_align_camera('cam1')

   def __cb_align_cam2_clicked(self):
      if self.__ui.pushButton_video2_align.text() == 'Align Camera':
         self.__align_logic.start_align_camera('cam2')
      else:
         self.__align_logic.stop_align_camera('cam2')

   def __evt_alignlogic_align_start(self, cam):
      self.enable_all_gui_elements(False)
      if cam == 'cam1':
         self.__ui.pushButton_video1_align.setText('Stop')
         self.__ui.pushButton_video2_align.setEnabled(False)
      else:
         self.__ui.pushButton_video2_align.setText('Stop')
         self.__ui.pushButton_video1_align.setEnabled(False)

   def __evt_alignlogic_align_stop(self, cam):
      self.enable_all_gui_elements(True)

      self.__ui.pushButton_video1_align.setText('Align Camera')
      self.__ui.pushButton_video2_align.setText('Align Camera')
      
      if self.__camera_server.is_online('cam1'): 
         self.__ui.pushButton_video1_align.setEnabled(True)
      if self.__camera_server.is_online('cam2'): 
         self.__ui.pushButton_video2_align.setEnabled(True)

      ''' Check status for start stop buttons '''
      self.__ui.pushbutton_stop.setEnabled(False)
      if not self.__camera_server.is_ready_to_shoot():
         self.__ui.pushbutton_start.setEnabled(False)


   def __evt_alignlogic_align_new_frame(self, frame :Frame):
      self.display_frame(frame)

   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Game GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __cb_game_changed(self, index):
      if index == 0: self.__globals.set_game(Globals.GAME_SPEED_TRAP)
      if index == 1: self.__globals.set_game(Globals.GAME_GATE_CRASHER)

   def __evt_globals_game_change(self, game):
      print(game)

   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Flight GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __cb_flight(self):
      for i in range(0,20):
         if self.__ui.radio_buttons_flights[i].isChecked(): break
      self.__globals.set_flight(i + 1)

   def __evt_globals_flight_change(self, flight):
      self.__ui.radio_buttons_flights[flight - 1].setChecked(True)
      self.__load_flight(flight)

   def __load_flight(self, flight):
      self.__ui.radio_buttons_flights[flight - 1].setChecked(True)

      self.__ui.slider_video['cam1'].setMaximum(1 if not self.__video_player.get_last_frame("cam1") else (self.__video_player.get_last_frame('cam1').get_position() or 1))
      self.__ui.slider_video['cam2'].setMaximum(1 if not self.__video_player.get_last_frame("cam2") else (self.__video_player.get_last_frame('cam2').get_position() or 1))
      self.__video_player.set_position('cam1', 1)
      self.__video_player.set_position('cam2', 1)

   def __cb_distance_changed(self, value):
      try:
         value = int(value)
      except:
         value = 100
      self.__speed_logic.set_distance(value)

   ''' ground level GUI '''
   def __cb_groundlevel_changed(self, value):
      self.__globals.set_ground_level(value)

   def __evt_globals_ground_level_change(self, value):
      ''' When the ground level change the videos needs to redraw '''
      self.display_frame(self.__video_player.get_current_frame('cam1'))
      self.display_frame(self.__video_player.get_current_frame('cam2'))

      ''' Do not try to set position if we are currently dragging '''
      if self.__ui.verticalSlider_groundlevel.isSliderDown() == False:
         self.__ui.verticalSlider_groundlevel.setValue(value)


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Speed GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __cb_start_cameras(self):
      try:
         self.__speed_logic.start_run()
      except IllegalStateError as e:
         logger.error(e)

   def __cb_stop_cameras(self):
      self.__speed_logic.stop_run()

   def __evt_speedlogic_speed_start(self):
      self.__speed_logic_model_announcements.clear()
      self.__speedlogic_average_update_gui()
      self.__speedlogic_speed_update_gui(None)
      self.enable_all_gui_elements(False)
      self.__ui.pushbutton_stop.setEnabled(True)
      self.__ui.pushButton_video1_align.setEnabled(False)
      self.__ui.pushButton_video2_align.setEnabled(False)
      self.__ui.pushbutton_stop.setEnabled(True)

   def __evt_speedlogic_speed_stop(self):
      ''' Stop event for speed logic'''

      ''' Load the just stopped flight, this will load the video player etc. '''
      self.__globals.set_flight(self.__globals.get_flight())

      self.enable_all_gui_elements(True)
      self.__ui.pushbutton_stop.setEnabled(False)
      self.__ui.pushButton_video1_align.setEnabled(True)
      self.__ui.pushButton_video2_align.setEnabled(True)

   def __evt_speedlogic_speed_new_frame(self, frame: Frame):
      ''' Only display every third frame when live trackng - 30 fps '''
      if self.__ui.checkBox_live.isChecked() and frame.get_position() % 3 == 0:
         self.display_frame(frame)

      ''' Display time '''
      self.__ui.label_time_video[frame.get_cam()].setText(
         self.__format_video_time(
            self.__speed_logic.get_time(frame)
         )
      )

   def __evt_speedlogic_pass_abort(self):
      self.__sound.play_error()

   def __evt_speedlogic_pass_start(self, cam):
      self.__sound.play_gate_1()

   def __evt_speedlogic_pass_end(self, speed_pass_message: SpeedPassMessage):
      self.__sound.play_gate_2()

   def __speedlogic_append_row(self, announcement: Announcement):
      out = ("--> " if (announcement.get_direction() == 1) else "<-- ") + \
         "%.3f" % (float(announcement.get_duration()) / 1000) + " - %d" % announcement.get_speed() + " km/h "
      self.__speed_logic_model_announcements.appendRow(QtGui.QStandardItem(out))

   def __evt_speedlogic_announcement_new(self, announcement: Announcement):
      self.__speedlogic_append_row(announcement)
      if self.__ui.checkBox_speak.isChecked():
         ''' Speak speed one second after second gate signal '''
         self.__sound.play_number(int(announcement.get_speed()), 1000)

      self.__speedlogic_speed_update_gui(announcement)
      self.__speedlogic_average_update_gui()

   def __evt_speedlogic_announcement_load(self, announcements: Announcements):
      self.__speed_logic_model_announcements.clear()
      for announcement in announcements.get_announcements():
         self.__speedlogic_append_row(announcement)
      self.__speedlogic_average_update_gui()
      self.__speedlogic_speed_update_gui(None)

   def __speedlogic_speed_update_gui(self, announcement: Announcement):
      if announcement is None:
         self.__ui.label_time.setText('Time: ---')
         self.__ui.label_speed.setText('Speed: ---')
         return

      ''' Set speed from camera frame numbers '''
      duration_sec = announcement.get_duration() / 1000
      speed_kmh = self.__speed_logic.get_distance() / (announcement.get_duration() / 1000) * 3.6
      self.__ui.label_time.setText("Time: %.3f" % duration_sec + "sec")
      self.__ui.label_speed.setText("Speed: %d" % speed_kmh + " km/h")

   def __speedlogic_average_update_gui(self):
      ''' update the average speed GUI '''
      max_speeds = self.__speed_logic.get_announcement_max_speeds()

      if max_speeds['LEFT'] == None or max_speeds['RIGHT'] == None:
         self.__ui.label_average.setText('Average: ---')
         return
      average_speed = (max_speeds['LEFT'].get_speed() + max_speeds['RIGHT'].get_speed()) / 2 
      self.__ui.label_average.setText("Average: %.1f mk/h" % average_speed)

   def __cb_speed_logic_announcement_changed(self, evt):
      self.__video_player.stop_all()
      announcement = self.__speed_logic.get_announcement_by_index(evt.row())
      self.__video_player.set_position('cam1', announcement.get_cam1_position())
      self.__video_player.set_position('cam2', announcement.get_cam2_position())
      self.__speedlogic_speed_update_gui(announcement)

   def __cb_remove_announcement_clicked(self, evt):
      index = self.__ui.listView_anouncements.currentIndex().row()
      if index == -1:
         QMessageBox.information(self, 'Sleipnir Information', 'Select announcement to delete')
         return
      ret = QMessageBox.question(self, 'Sleipnir Information', "Confirm removing announcement", QMessageBox.Ok | QMessageBox.Cancel)
      if ret == QMessageBox.Cancel: return
      self.__speed_logic_model_announcements.removeRow(index)

      ''' Remove both from actual index, and model for list 
      The actual index is used when valulating average '''
      self.__speed_logic.remove_announcement_by_index(index)
      self.__speedlogic_average_update_gui()
      current_row = self.__ui.listView_anouncements.currentIndex().row()
      if (current_row == -1):
         self.__speedlogic_speed_update_gui(None)
      else:
         self.__speedlogic_speed_update_gui(self.__speed_logic.get_announcement_by_index(current_row))

   def display_frame(self, frame :Frame):
      ''' display video frame '''
      image = frame.pop_image_load_if_missing(self.__db)

      # Draw center line
      cv.rectangle(image, (160, 0), (160, 480), (0, 0, 0), 1)
      # Draw ground level
      cv.rectangle(image, (0, self.__globals.get_ground_level()), (320, self.__globals.get_ground_level()), (0, 0, 0), 1)

      image_qt = QtGui.QImage(image, image.shape[1], image.shape[0], image.strides[0], QtGui.QImage.Format_Indexed8)
      self.__ui.widget_video[frame.get_cam()].setPixmap(QtGui.QPixmap.fromImage(image_qt))






   def enable_all_gui_elements(self, enabled):
      self.__enable_video_ui(enabled)

      self.__ui.pushbutton_stop.setEnabled(enabled)
      self.__ui.pushbutton_start.setEnabled(enabled)
      self.__ui.checkBox_speak.setEnabled(enabled)
      self.__ui.listView_anouncements.setEnabled(enabled)
      self.__ui.verticalSlider_groundlevel.setEnabled(enabled)

      self.__ui.lineEdit_distance.setEnabled(enabled)
      self.__ui.checkBox_live.setEnabled(enabled)
      self.__ui.pushButton_remove_announcement.setEnabled(enabled)

      for i in range(0, len(self.__ui.radio_buttons_flights)):
         self.__ui.radio_buttons_flights[i].setEnabled(enabled)



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
