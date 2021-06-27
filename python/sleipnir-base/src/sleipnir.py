from typing import List
import sys
import time

from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QAbstractItemView, QApplication, QMainWindow, QMessageBox
import cv2 as cv

from sleipnir_window import SleipnirWindow
from game.speed_trap.logic import SpeedLogic, SpeedPassMessage
from game.gate_crasher.logic import GateCrasherLogic
from configuration import Configuration, ConfigurationError
from database.db import DB
from game.speed_trap.announcement import Announcements, Announcement
from game.gate_crasher.announcement import Announcement as GateCrasherAnnouncement
from frame import Frame
from camera_server import CameraServer
from globals import Globals
from align_logic import AlignLogic
from video_player import VideoPlayer
from sound import Sound
from game import speed_trap
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

      ''' Initalize components '''
      self.__globals = Globals(self.__db)
      self.__camera_server = CameraServer(self.__globals)
      self.__video_player = VideoPlayer(self.__globals, self, self.__configuration)
      self.__align_logic = AlignLogic(self.__globals, self.__camera_server)
      self.__speed_logic = SpeedLogic(self.__globals, self.__camera_server, self.__configuration)
      self.__gate_crasher_logic = GateCrasherLogic(self.__globals, self.__camera_server, self.__configuration)

      ''' Start camera server '''
      self.__camera_server.start_server(self.__db)
      event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_cameraserver_camera_online)
      event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_cameraserver_camera_offline)
      self.__ui.label_video1_online.setText("Cam1: Offline")
      self.__ui.label_video2_online.setText("Cam2: Offline")

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

      self.__speed_trap_gui = speed_trap.gui(self.__ui)

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
      self.__ui.pushButton_remove_announcement.clicked.connect(self.__cb_remove_announcement_clicked)
      self.__speed_logic_model_result = QtGui.QStandardItemModel()
      self.__speed_logic_init_model_result()
      self.__ui.table_view_speed_trap_announcement.setModel(self.__speed_logic_model_result)
      self.__ui.table_view_speed_trap_announcement.setSelectionBehavior(QAbstractItemView.SelectRows)
      self.__ui.table_view_speed_trap_announcement.clicked.connect(self.__cb_speed_logic_announcement_changed)

      ''' Gate Crasher callbacks and events '''
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_START, self.__evt_gatecrasherlogic_run_start)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_STOP, self.__evt_gatecrasherlogic_run_stop)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_FINISH, self.__evt_gatecrasherlogic_run_finish)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_NEW_FRAME, self.__evt_gatecrasherlogic_run_new_frame)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_HIT_GATE, self.__evt_gatecrasherlogic_run_hit_gate)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_RESTART, self.__evt_gatecrasherlogic_run_restart)
      self.__gatecrasher_logic_model_result = QtGui.QStandardItemModel()
      self.__gate_crasher_init_model_result()
      self.__ui.table_view_gate_crasher_result.setModel(self.__gatecrasher_logic_model_result)
      self.__ui.table_view_gate_crasher_result.setSelectionBehavior(QAbstractItemView.SelectRows)
      event.on(GateCrasherLogic.EVENT_GATE_CRASHER_ANNOUNCEMENT_LOAD, self.__evt_gatecrasherlogic_announcement_load)
      self.__ui.table_view_gate_crasher_result.clicked.connect(self.__cb_gate_crasher_announcement_changed)
      self.__ui.combo_box_gate_crasher_level_select.addItems(self.__gate_crasher_logic.get_level_names())
      self.__ui.combo_box_gate_crasher_level_select.currentIndexChanged.connect(self.__cb_gate_crasher_level_select_changed)

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
         self.__ui.label_video2_online.setText("Cam2: Online")

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
      return "%02d:%02d.%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)

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
      self.__ui.stacked_widget_game.setCurrentIndex(
         {
            self.__globals.GAME_SPEED_TRAP: 0,
            self.__globals.GAME_GATE_CRASHER: 1
         }[game]
      )

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

   def __speed_logic_init_model_result(self):
      self.__speed_logic_model_result.clear()
      self.__speed_logic_model_result.setHorizontalHeaderLabels(["", "Dir", "Time", "Speed"])
      self.__ui.table_view_speed_trap_announcement.setColumnWidth(0, 30)

   def __cb_start_cameras(self):
      try:
         if self.__globals.get_game() == Globals.GAME_SPEED_TRAP:
            self.__speed_logic.start_run()
         if self.__globals.get_game() == Globals.GAME_GATE_CRASHER:
            self.__gate_crasher_logic.start_run()
      except IllegalStateError as e:
         logger.error(e)

   def __cb_stop_cameras(self):
      try:
         if self.__globals.get_game() == Globals.GAME_SPEED_TRAP:
            self.__speed_logic.stop_run()
         if self.__globals.get_game() == Globals.GAME_GATE_CRASHER:
            self.__gate_crasher_logic.stop_run()
      except IllegalStateError as e:
         logger.error(e)

   def __evt_speedlogic_speed_start(self):
      self.__ui.slider_video['cam1'].setSliderPosition(0)
      self.__ui.slider_video['cam2'].setSliderPosition(0)
      self.__speed_logic_init_model_result()
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
      self.__sound.play_beep()

   def __evt_speedlogic_pass_end(self, speed_pass_message: SpeedPassMessage):
      self.__sound.play_beep_beep()

   def __speedlogic_append_row(self, announcement: Announcement):
      out = []
      item = QtGui.QStandardItem(str(self.__speed_logic_model_result.rowCount() + 1))
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem("-->" if announcement.get_direction() == 1 else "<--")
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem("%.3f" % (announcement.get_duration() / 1000))
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem("%.1f" % announcement.get_speed())
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      self.__speed_logic_model_result.appendRow(out)
      self.__ui.table_view_speed_trap_announcement.setRowHeight(self.__speed_logic_model_result.rowCount() - 1, 18)

   def __evt_speedlogic_announcement_new(self, announcement: Announcement):
      self.__speedlogic_append_row(announcement)
      if self.__ui.checkBox_speak.isChecked():
         ''' Speak speed one second after second gate signal '''
         self.__sound.play_number(int(announcement.get_speed()), 1000)

      self.__speedlogic_speed_update_gui(announcement)
      self.__speedlogic_average_update_gui()

   def __evt_speedlogic_announcement_load(self, announcements: Announcements):
      self.__speed_logic_init_model_result()
      for announcement in announcements.get_announcements():
         self.__speedlogic_append_row(announcement)
      self.__speedlogic_average_update_gui()
      self.__speedlogic_speed_update_gui(None)

   def __speedlogic_speed_update_gui(self, announcement: Announcement):
      if announcement is None:
         self.__ui.label_time.setText('Time:    ---')
         self.__ui.label_speed.setText('Speed:   ---')
         return

      ''' Set speed from camera frame numbers '''
      duration_sec = announcement.get_duration() / 1000
      speed_kmh = self.__speed_logic.get_distance() / (announcement.get_duration() / 1000) * 3.6
      self.__ui.label_time.setText("Time:    %.3f sec" % duration_sec)
      self.__ui.label_speed.setText("Speed:   %.1f km/h" % speed_kmh)

   def __speedlogic_average_update_gui(self):
      ''' update the average speed GUI '''
      max_speeds = self.__speed_logic.get_announcement_max_speeds()

      if max_speeds['LEFT'] == None or max_speeds['RIGHT'] == None:
         self.__ui.label_average.setText('Average: ---')
         return
      average_speed = (max_speeds['LEFT'].get_speed() + max_speeds['RIGHT'].get_speed()) / 2 
      self.__ui.label_average.setText("Average: %.1f km/h" % average_speed)

   def __cb_speed_logic_announcement_changed(self, evt):
      self.__video_player.stop_all()
      announcement = self.__speed_logic.get_announcement_by_index(evt.row())
      self.__video_player.set_position('cam1', announcement.get_cam1_position())
      self.__video_player.set_position('cam2', announcement.get_cam2_position())
      self.__speedlogic_speed_update_gui(announcement)

   def __cb_remove_announcement_clicked(self, evt):
      index = self.__ui.table_view_speed_trap_announcement.currentIndex().row()
      if index == -1:
         QMessageBox.information(self, 'Sleipnir Information', 'Select announcement to delete')
         return
      ret = QMessageBox.question(self, 'Sleipnir Information', "Confirm removing announcement", QMessageBox.Ok | QMessageBox.Cancel)
      if ret == QMessageBox.Cancel: return
      self.__speed_logic_model_result.removeRow(index)

      ''' Remove both from actual index, and model for list 
      The actual index is used when valulating average '''
      self.__speed_logic.remove_announcement_by_index(index)
      self.__speedlogic_average_update_gui()
      current_row = self.__ui.table_view_speed_trap_announcement.currentIndex().row()
      if (current_row == -1):
         self.__speedlogic_speed_update_gui(None)
      else:
         self.__speedlogic_speed_update_gui(self.__speed_logic.get_announcement_by_index(current_row))

   def display_frame(self, frame :Frame):
      ''' display video frame '''
      image = frame.pop_image_load_if_missing(self.__db, self.__globals.get_game())

      # Draw center line
      cv.rectangle(image, (160, 0), (160, 480), (0, 0, 0), 1)
      # Draw ground level
      cv.rectangle(image, (0, self.__globals.get_ground_level()), (320, self.__globals.get_ground_level()), (0, 0, 0), 1)

      image_qt = QtGui.QImage(image, image.shape[1], image.shape[0], image.strides[0], QtGui.QImage.Format_Indexed8)
      self.__ui.widget_video[frame.get_cam()].setPixmap(QtGui.QPixmap.fromImage(image_qt))


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸    Gate Crasher GUI    ¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''

   def __gate_crasher_init_model_result(self):
      self.__gatecrasher_logic_model_result.clear()
      self.__gatecrasher_logic_model_result.setHorizontalHeaderLabels(["", "Gate", "Dir", "Gate Time"])
      self.__ui.table_view_gate_crasher_result.setColumnWidth(0, 30)

   def __cb_gate_crasher_level_select_changed(self, index):
      self.__gate_crasher_logic.set_level(index)

   def __evt_gatecrasherlogic_run_start(self):
      self.__ui.slider_video['cam1'].setSliderPosition(0)
      self.__ui.slider_video['cam2'].setSliderPosition(0)
      self.enable_all_gui_elements(False)
      self.__ui.pushbutton_stop.setEnabled(True)
      self.__ui.pushButton_video1_align.setEnabled(False)
      self.__ui.pushButton_video2_align.setEnabled(False)
      self.__ui.pushbutton_stop.setEnabled(True)
      self.__gate_crasher_init_model_result()

   def __evt_gatecrasherlogic_run_stop(self):
      ''' Stop event for gate crasher logic'''

      ''' Load the just stopped flight, this will load the video player etc. '''
      self.__globals.set_flight(self.__globals.get_flight())

      self.enable_all_gui_elements(True)
      self.__ui.pushbutton_stop.setEnabled(False)
      self.__ui.pushButton_video1_align.setEnabled(True)
      self.__ui.pushButton_video2_align.setEnabled(True)

   def __evt_gatecrasherlogic_run_restart(self):
      self.__gate_crasher_init_model_result()
      self.__sound.play_error()

   def __evt_gatecrasherlogic_run_hit_gate(self, announcement: GateCrasherAnnouncement):
      self.__sound.play_beep_beep()
      self.__gatecrasherlogic_append_row(announcement)

      level = self.__gate_crasher_logic.get_levels()[self.__gate_crasher_logic.get_level()]

      try:
         hitpoint = level.get_hitpoint(announcement.get_gate_number() + 1)
      except IndexError:
         ''' No more gates in level '''
         return

      if hitpoint.get_cam() == 'cam1':
         self.__sound.play_gate_1(500)
      else:
         self.__sound.play_gate_2(500)

      if hitpoint.get_direction() == 'RIGHT':
         self.__sound.play_right(1000)
      else:
         self.__sound.play_left(1000)


   def __evt_gatecrasherlogic_run_finish(self, time_ms):
      ''' Display run time '''
      finish_time_str = self.__format_video_time(time_ms)

      self.__ui.label_gate_crasher_time.setText('Time: %s' % finish_time_str)
      self.__sound.play_cross_the_finish_line(500)

      minutes = int(finish_time_str[0:2])
      seconds = int(finish_time_str[3:5])
      milli_seconds1 = finish_time_str[6:7]
      milli_seconds2 = finish_time_str[7:8]
      milli_seconds3 = finish_time_str[8:9]
      self.__sound.play_number(minutes, 2000)
      self.__sound.play_number(seconds, 3200)
      self.__sound.play_number(milli_seconds1, 4400)
      self.__sound.play_number(milli_seconds2, 5000)
      self.__sound.play_number(milli_seconds3, 5600)


   def __gatecrasherlogic_append_row(self, gate_crasher_announcement: GateCrasherAnnouncement):
      out = []
      item = QtGui.QStandardItem(str(gate_crasher_announcement.get_gate_number() + 1))
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem('Left' if gate_crasher_announcement.get_cam() == 'cam1' else 'Right')
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem("-->" if gate_crasher_announcement.get_direction() == 'RIGHT' else "<--")
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      item = QtGui.QStandardItem(self.__format_video_time(gate_crasher_announcement.get_time_ms())[3:])
      item.setTextAlignment(QtCore.Qt.AlignCenter)
      out.append(item)
      self.__gatecrasher_logic_model_result.appendRow(out)
      self.__ui.table_view_gate_crasher_result.setRowHeight(self.__gatecrasher_logic_model_result.rowCount() - 1, 18)

   def __evt_gatecrasherlogic_announcement_load(self, announcements: List[GateCrasherAnnouncement]):
      self.__gate_crasher_init_model_result()
      finish_time = 0
      for announcement in announcements:
         level_index = self.__gate_crasher_logic.level_index_by_name(announcement.get_level_name())
         self.__ui.combo_box_gate_crasher_level_select.setCurrentIndex(level_index or 0)
         self.__gatecrasherlogic_append_row(announcement)
         finish_time += announcement.get_time_ms()
         self.__ui.label_gate_crasher_time.setText('Time: ' + 
            self.__format_video_time(finish_time)
         )

   def __cb_gate_crasher_announcement_changed(self, evt):
      self.__video_player.stop_all()
      announcement = self.__gate_crasher_logic.get_announcement_by_index(evt.row())
      self.__video_player.set_position('cam1', announcement.get_position())
      self.__video_player.set_position('cam2', announcement.get_position())

   def __evt_gatecrasherlogic_run_new_frame(self, frame: Frame):
      ''' Only display every third frame when live trackng - 30 fps '''
      if self.__ui.checkBox_live.isChecked() and frame.get_position() % 3 == 0:
         self.display_frame(frame)

      ''' Display time in videos '''
      self.__ui.label_time_video[frame.get_cam()].setText(
         self.__format_video_time(
            self.__gate_crasher_logic.get_time(frame)
         )
      )

      ''' Display run time '''
      self.__ui.label_gate_crasher_time.setText('Time: ' + 
         self.__format_video_time(self.__gate_crasher_logic.get_current_runtime())
      )
      



   def enable_all_gui_elements(self, enabled):
      self.__enable_video_ui(enabled)

      self.__ui.combo_box_game_select.setEnabled(enabled)
      self.__ui.combo_box_gate_crasher_level_select.setEnabled(enabled)
      self.__ui.table_view_gate_crasher_result.setEnabled(enabled)

      self.__ui.pushbutton_stop.setEnabled(enabled)
      self.__ui.pushbutton_start.setEnabled(enabled)
      self.__ui.checkBox_speak.setEnabled(enabled)
      self.__ui.table_view_speed_trap_announcement.setEnabled(enabled)
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
