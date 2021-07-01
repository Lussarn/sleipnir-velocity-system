from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QAbstractItemView

from globals import Globals
import event
from errors import *
from sound import Sound
from ui_sleipnir_window import Ui_SleipnirWindow
from configuration import Configuration
from camera_server import CameraServer
from video_player.video_player import VideoPlayer
from video_player.video_player_gui import VideoPlayerGUI
from frame.frame import Frame

from game.gate_crasher.logic import Logic
from game.gate_crasher.announcement import Announcement
from game.gate_crasher.events import *

import logging
import logger

logger = logging.getLogger(__name__)

class GUI:
    def __init__(self, win):
        from sleipnir import SleipnirWindow
        self.__win = win                                        # type: SleipnirWindow
        self.__ui = win.get_ui()                                # type: Ui_SleipnirWindow
        self.__sound = win.get_sound()                          # type: Sound
        self.__globals = win.get_globals()                      # type: Globals
        self.__camera_server = win.get_camera_server()          # type: CameraServer
        self.__configuration = win.get_configuration()          # type: Configuration
        self.__video_player = win.get_video_player()            # type: VideoPlayer
        self.__video_player_gui = win.get_video_player_gui()    # type: VideoPlayerGUI

        self.__logic = Logic(self.__globals, self.__camera_server, self.__configuration)

        from sleipnir import SleipnirWindow
        ''' Game start/stop events '''
        event.on(SleipnirWindow.EVENT_GAME_START_REQUESTED, self.__evt_SleipnirWindow_GAME_START_REQUESTED)
        event.on(SleipnirWindow.EVENT_GAME_STOP_REQUESTED, self.__evt_SleipnirWindow_GAME_STOP_REQUESTED)

        ''' Gate Crasher callbacks and events '''
        event.on(EVENT_GAME_STARTED, self.__evt_game_started)
        event.on(EVENT_GAME_STOPPED, self.__evt_game_stopped)
        event.on(EVENT_FRAME_NEW, self.__evt_frame_new)
        event.on(EVENT_COURSE_FINISHED, self.__evt_course_finished)
        event.on(EVENT_COURSE_HIT_GATE, self.__evt_course_hit_gate)
        event.on(EVENT_COURSE_RESTARTED, self.__evt_course_restart)
        self.__model_announcement = QtGui.QStandardItemModel()
        self.__model_announcement_reset()
        self.__ui.gate_crasher_table_view_result.setModel(self.__model_announcement)
        self.__ui.gate_crasher_table_view_result.setSelectionBehavior(QAbstractItemView.SelectRows)
        event.on(EVENT_ANNOUNCEMENT_LOADED, self.__evt_announcement_loaded)
        self.__ui.gate_crasher_table_view_result.clicked.connect(self.__cb_announcement_changed)
        self.__ui.gate_crasher_combo_box_course_select.addItems(self.__logic.get_level_names())
        self.__ui.gate_crasher_combo_box_course_select.currentIndexChanged.connect(self.__cb_course_select_changed)

    def __evt_SleipnirWindow_GAME_START_REQUESTED(self, game):
        try:
            if game == Globals.GAME_GATE_CRASHER: self.__logic.start_run()
        except IllegalStateError as e:
            logger.error(e)

    def __evt_SleipnirWindow_GAME_STOP_REQUESTED(self):
        try:
            if self.__globals.get_game() == Globals.GAME_GATE_CRASHER: self.__logic.stop_run()
        except IllegalStateError as e:
            logger.error(e)

    def __evt_game_started(self):
        self.__ui.slider_video['cam1'].setSliderPosition(0)
        self.__ui.slider_video['cam2'].setSliderPosition(0)
        self.__win.game_started()
        self.__model_announcement_reset()

    def __evt_game_stopped(self):
        ''' Stop event for gate crasher logic'''

        ''' Load the just stopped flight, this will load the video player etc. '''
        self.__globals.set_flight(self.__globals.get_flight())
        self.__win.game_stopped()

    def __evt_frame_new(self, frame: Frame):
        ''' Only display every third frame when live trackng - 30 fps '''
        if self.__ui.checkBox_live.isChecked() and frame.get_position() % 3 == 0:
            self.__video_player_gui.display_frame(frame)
        else:
            ''' pop image from frame to prevent memory leak '''
            frame.pop_image_load_if_missing(self.__globals.get_db(), self.__globals.get_game())

        ''' Display run time '''
        self.__ui.gate_crasher_label_time.setText('Time: %s' % self.__win.format_time(self.__logic.get_current_runtime()))

        ''' Display time beneath video '''
        self.__video_player_gui.video_display_frame_time(frame.get_cam(), self.__logic.get_time(frame))

    def __evt_course_restart(self):
        self.__model_announcement_reset()
        self.__sound.play_error()

    def __evt_course_finished(self, time_ms):
        ''' Display run time '''
        finish_time_str = self.__win.format_time(time_ms)

        self.__ui.gate_crasher_label_time.setText('Time: %s' % finish_time_str)
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

    def __evt_course_hit_gate(self, announcement: Announcement):
        self.__sound.play_beep_beep()
        self.__gatecrasherlogic_append_row(announcement)

        level = self.__logic.get_levels()[self.__logic.get_level()]

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

    def __evt_announcement_loaded(self, announcements: list[Announcement]):
        self.__model_announcement_reset()
        finish_time = 0
        for announcement in announcements:
            level_index = self.__logic.level_index_by_name(announcement.get_level_name())
            self.__ui.gate_crasher_combo_box_course_select.setCurrentIndex(level_index or 0)
            self.__gatecrasherlogic_append_row(announcement)
            finish_time += announcement.get_time_ms()
            self.__ui.gate_crasher_label_time.setText('Time: ' + 
                self.__win.format_time(finish_time)
            )


    def __model_announcement_reset(self):
        self.__model_announcement.clear()
        self.__model_announcement.setHorizontalHeaderLabels(["", "Gate", "Dir", "Gate Time"])
        self.__ui.gate_crasher_table_view_result.setColumnWidth(0, 30)

    def __cb_course_select_changed(self, index):
        self.__logic.set_level(index)

    def __cb_announcement_changed(self, evt):
        self.__video_player.stop_all()
        announcement = self.__logic.get_announcement_by_index(evt.row())
        self.__video_player.set_position('cam1', announcement.get_position())
        self.__video_player.set_position('cam2', announcement.get_position())

    def __gatecrasherlogic_append_row(self, gate_crasher_announcement: Announcement):
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
        item = QtGui.QStandardItem(self.__win.format_time(gate_crasher_announcement.get_time_ms())[3:])
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        out.append(item)
        self.__model_announcement.appendRow(out)
        self.__ui.gate_crasher_table_view_result.setRowHeight(self.__model_announcement.rowCount() - 1, 18)

    def enable_gui_elements(self, enabled: bool):
      self.__ui.gate_crasher_combo_box_course_select.setEnabled(enabled)
      self.__ui.gate_crasher_table_view_result.setEnabled(enabled)
