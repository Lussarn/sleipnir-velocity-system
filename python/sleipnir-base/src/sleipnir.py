from typing import List
import sys

from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox

from ui_sleipnir_window import Ui_SleipnirWindow
from configuration import Configuration, ConfigurationError
from database.db import DB
from camera_server import CameraServer
from globals import Globals
from video_player.video_player import VideoPlayer
from video_player.video_player_gui import VideoPlayerGUI
from sound import Sound
from game.align.gui import GUI as AlignGUI
from game.speed_trap.gui import GUI as SpeedTrapGUI
from game.gate_crasher.gui import GUI as GateCrasherGUI
from errors import *

from game.align.events import *
from game.align.logic import Logic as AlignLogic

import logging
import logger

logger = logging.getLogger(__name__)

import event

'''
SleipnirWindow emits the following events

SleipnirWindow.GAME_START_REQUESTED : str               : A game have been requested to start 
SleipnirWindow.GAME_STOP_REQUESTED                      : SleipnirWindow have requested to stop ongoing game
'''

class SleipnirWindow(QMainWindow):
   EVENT_GAME_START_REQUESTED           = "sleipnir_window.game.start"
   EVENT_GAME_STOP_REQUESTED            = "sleipnir_window.game.stop"

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
      self.__ui = Ui_SleipnirWindow()
      self.__ui.setupUi(self)
      self.setWindowTitle("Sleipnir Velocity - Go Fast!")

      ''' Initalize components '''
      self.__globals = Globals(self.__db)
      self.__camera_server = CameraServer(self.__globals)
      self.__video_player = VideoPlayer(self.__globals, self, self.__configuration)
      self.__video_player_gui = VideoPlayerGUI(self, self.__video_player)
      self.__align_logic = AlignLogic(self.__globals, self.__camera_server)

      ''' Start camera server '''
      self.__camera_server.start_server(self.__db)
      event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_cameraserver_camera_online)
      event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_cameraserver_camera_offline)
      self.__ui.label_video1_online.setText("Cam1: Offline")
      self.__ui.label_video2_online.setText("Cam2: Offline")

      ''' game callbacks and events '''
      event.on(Globals.EVENT_GAME_CHANGE, self.__evt_globals_game_change)
      self.__ui.sleipnir_combo_box_game_select.currentIndexChanged.connect(self.__cb_game_changed)

      ''' flight callbacks and events '''
      for radio_buttons_flight in self.__ui.radio_buttons_flights:
         radio_buttons_flight.clicked.connect(self.__cb_flight)
      event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

      ''' ground level callbacks and events '''
      self.__ui.verticalSlider_groundlevel.valueChanged.connect(self.__cb_groundlevel_changed)
      event.on(Globals.EVENT_GROUND_LEVEL_CHANGE, self.__evt_globals_ground_level_change)

      ''' Align callbacks and events '''
      self.__ui.align_push_button_video1.clicked.connect(self.__cb_align_cam1_clicked)
      self.__ui.align_push_button_video2.clicked.connect(self.__cb_align_cam2_clicked)
      self.__ui.align_push_button_video1.setEnabled(False)
      self.__ui.align_push_button_video2.setEnabled(False)

      ''' Start/Stop Cameras'''
      self.__ui.sleipnir_push_button_start.setEnabled(False)
      self.__ui.sleipnir_push_button_start.clicked.connect(self.__cb_start_cameras)
      self.__ui.sleipnir_push_button_stop.setEnabled(False)
      self.__ui.sleipnir_push_button_stop.clicked.connect(self.__cb_stop_cameras)

      ''' Initialize align game '''
      self.__align_gui = AlignGUI(self)

      ''' Initialize speed trap game '''
      self.__speed_trap_gui = SpeedTrapGUI(self)

      ''' Initialize gate crasher game '''
      self.__gate_crasher_gui = GateCrasherGUI(self)

      ''' Currently selected Game GUI '''
      self.__current_game_gui = self.__speed_trap_gui

      ''' load flight number 1 '''
      self.__globals.set_flight(1)

      ''' Show GUI '''
      self.show()
      self.raise_()

   def __del__(self):
      logger.debug("Mainwindow destructor called")
      if self.__db is not None:
         self.__db.stop()

   def get_globals(self) -> Globals:
      return self.__globals

   def get_ui(self) -> Ui_SleipnirWindow:
      return self.__ui

   def get_sound(self) -> Sound:
      return self.__sound

   def get_camera_server(self) -> CameraServer:
      return self.__camera_server

   def get_configuration(self) -> Configuration:
      return self.__configuration

   def get_video_player(self) -> VideoPlayer:
      return self.__video_player

   def get_video_player_gui(self) -> VideoPlayerGUI:
      return self.__video_player_gui


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º    Camera Online GUI    ¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''
   def __evt_cameraserver_camera_online(self, cam):
      if (cam == 'cam1'):
         self.__ui.label_video1_online.setText("Cam1: Online")
         self.__ui.align_push_button_video1.setEnabled(True)
      else:
         self.__ui.align_push_button_video2.setEnabled(True)
         self.__ui.label_video2_online.setText("Cam2: Online")

      if self.__camera_server.is_ready_to_shoot():
         self.__ui.sleipnir_push_button_start.setEnabled(True)
         self.__ui.sleipnir_push_button_stop.setEnabled(False)
      
   def __evt_cameraserver_camera_offline(self, cam):
      if (cam == 'cam1'):
         self.__ui.label_video1_online.setText("Cam1: Offline")
         self.__ui.align_push_button_video1.setEnabled(False)
      else:
         self.__ui.label_video1_online.setText("Cam2: Offine")
         self.__ui.align_push_button_video2.setEnabled(False)

      self.__ui.sleipnir_push_button_start.setEnabled(False)
      self.__ui.sleipnir_push_button_stop.setEnabled(False)


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Align GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''
   def __cb_align_cam1_clicked(self):
      if self.__ui.align_push_button_video1.text() == 'Align':
         ''' Set game to ALIGN '''
         self.__globals.set_game(Globals.GAME_ALIGN)
         try:
            self.__align_logic.start_align_camera('cam1')
         except Exception as e:
            ''' Restore as align did not start as expected '''
            logger.error(e)
            self.__cb_game_changed(self.__ui.sleipnir_combo_box_game_select.currentIndex())
      else:
         self.__align_logic.stop_align_camera('cam1')
         self.__cb_game_changed(self.__ui.sleipnir_combo_box_game_select.currentIndex())

   def __cb_align_cam2_clicked(self):
      if self.__ui.align_push_button_video2.text() == 'Align':
         ''' Set game to ALIGN '''
         self.__globals.set_game(Globals.GAME_ALIGN)
         try:
            self.__align_logic.start_align_camera('cam2')
         except Exception as e:
            ''' Restore as align did not start as expected '''
            logger.error(e)
            self.__cb_game_changed(self.__ui.sleipnir_combo_box_game_select.currentIndex())
      else:
         self.__align_logic.stop_align_camera('cam2')
         ''' Restore game to what's in the game combobox '''
         self.__cb_game_changed(self.__ui.sleipnir_combo_box_game_select.currentIndex())


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø    Game GUI    ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''
   def __cb_start_cameras(self):
      event.emit(SleipnirWindow.EVENT_GAME_START_REQUESTED, self.__globals.get_game())

   def __cb_stop_cameras(self):
      event.emit(SleipnirWindow.EVENT_GAME_STOP_REQUESTED)

   def __cb_game_changed(self, index):
      if index == 0:
         self.__globals.set_game(Globals.GAME_SPEED_TRAP)
      if index == 1: 
         self.__globals.set_game(Globals.GAME_GATE_CRASHER)

   def __evt_globals_game_change(self, game):
      ''' Check if we are aligning, the we do not change the GUI '''
      if game == Globals.GAME_ALIGN: return

      ''' Show Correct Game GUI '''
      self.__ui.stacked_widget_game.setCurrentIndex(
         {
            self.__globals.GAME_SPEED_TRAP: 0,
            self.__globals.GAME_GATE_CRASHER: 1
         }[game]
      )

      self.__current_game_gui = {
         self.__globals.GAME_SPEED_TRAP: self.__speed_trap_gui,
         self.__globals.GAME_GATE_CRASHER: self.__gate_crasher_gui
      }[game]
      

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


      self.__ui.slider_video['cam1'].setMaximum(1 if not self.__video_player.get_last_frame('cam1') else (self.__video_player.get_last_frame('cam1').get_position() or 1))
      self.__ui.slider_video['cam2'].setMaximum(1 if not self.__video_player.get_last_frame('cam2') else (self.__video_player.get_last_frame('cam2').get_position() or 1))

      self.__video_player_gui.set_default_image('cam1')
      self.__video_player_gui.set_default_image('cam2')
      self.__video_player.set_position('cam1', 1)
      self.__video_player.set_position('cam2', 1)


   ''' ¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸    Ground Level GUI    ¸¸,ø¤º°`°º¤ø,¸¸,ø¤º°`°º¤ø,¸¸,ø '''
   def __cb_groundlevel_changed(self, value):
      self.__globals.set_ground_level(value)

   def __evt_globals_ground_level_change(self, value):
      ''' When the ground level change the videos needs to redraw '''
      self.__video_player_gui.display_frame(self.__video_player.get_current_frame('cam1'), 'cam1')
      self.__video_player_gui.display_frame(self.__video_player.get_current_frame('cam2'), 'cam2')

      ''' Do not try to set position if we are currently dragging '''
      if self.__ui.verticalSlider_groundlevel.isSliderDown() == False:
         self.__ui.verticalSlider_groundlevel.setValue(value)

   def game_started(self):
        self.enable_all_gui_elements(False)
        self.__ui.sleipnir_push_button_stop.setEnabled(True)
        self.__ui.align_push_button_video1.setEnabled(False)
        self.__ui.align_push_button_video2.setEnabled(False)


   def game_stopped(self):
      self.enable_all_gui_elements(True)
      self.__ui.sleipnir_push_button_stop.setEnabled(False)
      self.__ui.align_push_button_video1.setEnabled(True)
      self.__ui.align_push_button_video2.setEnabled(True)

   def enable_all_gui_elements(self, enabled):
      self.__video_player_gui.enable_gui_elements(enabled)
      self.__current_game_gui.enable_gui_elements(enabled)

      self.__ui.sleipnir_combo_box_game_select.setEnabled(enabled)
      self.__ui.sleipnir_push_button_stop.setEnabled(enabled)
      self.__ui.sleipnir_push_button_start.setEnabled(enabled)
      self.__ui.verticalSlider_groundlevel.setEnabled(enabled)
      
      self.__ui.checkBox_live.setEnabled(enabled)
      for i in range(0, len(self.__ui.radio_buttons_flights)):
         self.__ui.radio_buttons_flights[i].setEnabled(enabled)

   def format_time(self, ms):
      return "%02d:%02d.%03d" % (int(ms / 1000) / 60, int(ms / 1000) % 60, ms % 1000)



if __name__ == '__main__':
   import sys
   app = QApplication(sys.argv)
   try:
      window = SleipnirWindow()
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
