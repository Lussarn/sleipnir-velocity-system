from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QAbstractItemView, QMessageBox

from globals import Globals
import event
from errors import *
from sound import Sound
from ui_sleipnir_window import Ui_SleipnirWindow
from configuration import Configuration, ConfigurationError
from camera_server import CameraServer
from video_player import VideoPlayer
from frame import Frame

from game.speed_trap.logic import Logic, SpeedPassMessage
from game.speed_trap.announcement import Announcement, Announcements
from game.speed_trap.events import *

import logging
import logger

logger = logging.getLogger(__name__)

class GUI:
    def __init__(self, win):
        from sleipnir import SleipnirWindow
        self.__win = win                                # type: SleipnirWindow
        self.__ui = win.get_ui()                        # type: Ui_SleipnirWindow
        self.__sound = win.get_sound()                  # type: Sound
        self.__globals = win.get_globals()              # type: Globals
        self.__camera_server = win.get_camera_server()  # type: CameraServer
        self.__configuration = win.get_configuration()  # type: Configuration
        self.__video_player = win.get_video_player()    # type: VideoPlayer

        self.__logic = Logic(self.__globals, self.__camera_server, self.__configuration)

    def initialize(self):
        from sleipnir import SleipnirWindow
        ''' Game start/stop events '''
        event.on(SleipnirWindow.EVENT_GAME_START_REQUESTED, self.__evt_SleipnirWindow_GAME_START_REQUESTED)
        event.on(SleipnirWindow.EVENT_GAME_STOP_REQUESTED, self.__evt_SleipnirWindow_GAME_STOP_REQUESTED)

        ''' Speed Trap callbacks and events '''
        event.on(EVENT_GAME_STARTED, self.__evt_game_started)
        event.on(EVENT_GAME_STOPPED, self.__evt_game_stopped)
        event.on(EVENT_FRAME_NEW, self.__evt_frame_new)
        event.on(EVENT_PASS_STARTED, self.__evt_pass_started)
        event.on(EVENT_PASS_ENDED, self.__evt_pass_ended)
        event.on(EVENT_PASS_ABORTED, self.__evt_pass_aborted)
        self.__ui.speed_trap_line_edit_distance.setText(str(self.__logic.get_distance()))
        self.__ui.speed_trap_line_edit_distance.textChanged.connect(self.__cb_distance_changed)

        ''' Announcements '''
        event.on(EVENT_ANNOUNCEMENT_NEW, self.__evt_announcement_new)
        event.on(EVENT_ANNOUNCEMENT_LOADED, self.__evt_announcement_loaded)
        self.__ui.speed_trap_push_button_remove_announcement.clicked.connect(self.__cb_remove_announcement_clicked)
        self.__model_announcement = QtGui.QStandardItemModel()
        self.__reset_model_announcement()
        self.__ui.speed_trap_table_view_announcement.setModel(self.__model_announcement)
        self.__ui.speed_trap_table_view_announcement.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui.speed_trap_table_view_announcement.clicked.connect(self.__cb_announcement_changed)

    def __evt_SleipnirWindow_GAME_START_REQUESTED(self, game):
        try:
            if game == Globals.GAME_SPEED_TRAP: self.__logic.start_run()
        except IllegalStateError as e:
            logger.error(e)

    def __evt_SleipnirWindow_GAME_STOP_REQUESTED(self):
        try:
            if self.__globals.get_game() == Globals.GAME_SPEED_TRAP: self.__logic.stop_run()
        except IllegalStateError as e:
            logger.error(e)

    def __evt_game_started(self):
        self.__ui.slider_video['cam1'].setSliderPosition(0)
        self.__ui.slider_video['cam2'].setSliderPosition(0)
        self.__reset_model_announcement()
        self.__average_update_gui()
        self.__update_gui(None)
        self.__win.enable_all_gui_elements(False)
        self.__ui.pushbutton_stop.setEnabled(True)
        self.__ui.pushButton_video1_align.setEnabled(False)
        self.__ui.pushButton_video2_align.setEnabled(False)
        self.__ui.pushbutton_stop.setEnabled(True)

    def __evt_game_stopped(self):
        ''' Stop event for speed logic'''

        ''' Load the just stopped flight, this will load the video player etc. '''
        self.__globals.set_flight(self.__globals.get_flight())

        self.__win.enable_all_gui_elements(True)
        self.__ui.pushbutton_stop.setEnabled(False)
        self.__ui.pushButton_video1_align.setEnabled(True)
        self.__ui.pushButton_video2_align.setEnabled(True)

    def __evt_frame_new(self, frame: Frame):
        ''' Only display every third frame when live trackng - 30 fps '''
        if self.__ui.checkBox_live.isChecked() and frame.get_position() % 3 == 0:
            self.__win.display_frame(frame)

        ''' Display time beneath video '''
        self.__win.video_display_frame_time(frame.get_cam(), self.__logic.get_time(frame))

    def __evt_pass_started(self, cam):
        self.__sound.play_beep()

    def __evt_pass_ended(self, speed_pass_message: SpeedPassMessage):
        self.__sound.play_beep_beep()

    def __evt_pass_aborted(self):
        self.__sound.play_error()

    def __evt_announcement_new(self, announcement: Announcement):
        self.__append_row(announcement)
        if self.__ui.speed_trap_check_box_speak.isChecked():
            ''' Speak speed one second after second gate signal '''
            self.__sound.play_number(int(announcement.get_speed()), 1000)

        self.__update_gui(announcement)
        self.__average_update_gui()

    def __evt_announcement_loaded(self, announcements: Announcements):
        self.__reset_model_announcement()
        for announcement in announcements.get_announcements():
            self.__append_row(announcement)
        self.__average_update_gui()
        self.__update_gui(None)

    def __cb_distance_changed(self, value):
        try:
            value = int(value)
        except:
            value = 100
        self.__logic.set_distance(value)

    def __cb_announcement_changed(self, evt):
        self.__video_player.stop_all()
        announcement = self.__logic.get_announcement_by_index(evt.row())
        self.__video_player.set_position('cam1', announcement.get_cam1_position())
        self.__video_player.set_position('cam2', announcement.get_cam2_position())
        self.__update_gui(announcement)

    def __cb_remove_announcement_clicked(self, evt):
        index = self.__ui.speed_trap_table_view_announcement.currentIndex().row()
        if index == -1:
            QMessageBox.information(self, 'Sleipnir Information', 'Select announcement to delete')
            return
        ret = QMessageBox.question(self, 'Sleipnir Information', "Confirm removing announcement", QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Cancel: return
        self.__model_announcement.removeRow(index)

        ''' Remove both from actual index, and model for list 
        The actual index is used when valulating average '''
        self.__logic.remove_announcement_by_index(index)
        self.__average_update_gui()
        current_row = self.__ui.speed_trap_table_view_announcement.currentIndex().row()
        if (current_row == -1):
            self.__update_gui(None)
        else:
            self.__update_gui(self.__logic.get_announcement_by_index(current_row))

    def __reset_model_announcement(self):
        self.__model_announcement.clear()
        self.__model_announcement.setHorizontalHeaderLabels(["", "Dir", "Time", "Speed"])
        self.__ui.speed_trap_table_view_announcement.setColumnWidth(0, 30)

    def __append_row(self, announcement: Announcement):
        out = []
        item = QtGui.QStandardItem(str(self.__model_announcement.rowCount() + 1))
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
        self.__model_announcement.appendRow(out)
        self.__ui.speed_trap_table_view_announcement.setRowHeight(self.__model_announcement.rowCount() - 1, 18)

    def __update_gui(self, announcement: Announcement):
        if announcement is None:
            self.__ui.speed_trap_label_time.setText('Time:    ---')
            self.__ui.speed_trap_label_speed.setText('Speed:   ---')
            return

        ''' Set speed from camera frame numbers '''
        duration_sec = announcement.get_duration() / 1000
        speed_kmh = self.__logic.get_distance() / (announcement.get_duration() / 1000) * 3.6
        self.__ui.speed_trap_label_time.setText("Time:    %.3f sec" % duration_sec)
        self.__ui.speed_trap_label_speed.setText("Speed:   %.1f km/h" % speed_kmh)

    def __average_update_gui(self):
        ''' update the average speed GUI '''
        max_speeds = self.__logic.get_announcement_max_speeds()

        if max_speeds['LEFT'] == None or max_speeds['RIGHT'] == None:
            self.__ui.speed_trap_label_average.setText('Average: ---')
            return
        average_speed = (max_speeds['LEFT'].get_speed() + max_speeds['RIGHT'].get_speed()) / 2 
        self.__ui.speed_trap_label_average.setText("Average: %.1f km/h" % average_speed)

    def enable_gui_elements(self, enabled: bool):
      self.__ui.speed_trap_check_box_speak.setEnabled(enabled)
      self.__ui.speed_trap_table_view_announcement.setEnabled(enabled)
      self.__ui.speed_trap_line_edit_distance.setEnabled(enabled)
      self.__ui.speed_trap_push_button_remove_announcement.setEnabled(enabled)
