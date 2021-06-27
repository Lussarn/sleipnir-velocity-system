from PySide2 import QtGui, QtCore
from PySide2.QtWidgets import QAbstractItemView
import cv2 as cv

from globals import Globals
import event
from errors import *
from sound import Sound
from ui_sleipnir_window import Ui_SleipnirWindow
from configuration import Configuration, ConfigurationError
from camera_server import CameraServer
from frame import Frame

from video_player.video_player import VideoPlayer

import logging
import logger

logger = logging.getLogger(__name__)

class VideoPlayerGUI:
    def __init__(self, win, video_player :VideoPlayer):
        from sleipnir import SleipnirWindow
        self.__win = win                                # type: SleipnirWindow
        self.__ui = win.get_ui()                        # type: Ui_SleipnirWindow
        self.__sound = win.get_sound()                  # type: Sound
        self.__globals = win.get_globals()              # type: Globals
        self.__camera_server = win.get_camera_server()  # type: CameraServer
        self.__configuration = win.get_configuration()  # type: Configuration
        self.__video_player = video_player

        ''' video 1 '''
        self.__ui.video_player_push_button_video1_play_forward.clicked.connect(self.__cb_video1_play_forward_clicked)
        self.__ui.video_player_push_button_video1_play_reverse.clicked.connect(self.__cb_video1_play_reverse_clicked)
        self.__ui.video_player_push_button_video1_stop.clicked.connect(self.__cb_video1_stop_clicked)
        self.__ui.video_player_push_button_video1_step_forward.clicked.connect(self.__cb_video1_step_forward)
        self.__ui.video_player_push_button_video1_step_reverse.clicked.connect(self.__cb_video1_step_reverse)
        self.__ui.slider_video['cam1'].setMinimum(1)
        self.__ui.slider_video['cam1'].valueChanged.connect(self.__cb_video1_slider_changed)
        self.__ui.video_player_push_button_video1_copy.clicked.connect(self.__cb_video1_copy_clicked)
        self.__ui.video_player_push_button_video1_find.clicked.connect(self.__cb_video1_find_clicked)

        ''' video 2 '''
        self.__ui.video_player_push_button_video2_play_forward.clicked.connect(self.__cb_video2_play_forward_clicked)
        self.__ui.video_player_push_button_video2_play_reverse.clicked.connect(self.__cb_video2_play_reverse_clicked)
        self.__ui.video_player_push_button_video2_stop.clicked.connect(self.__cb_video2_stop_clicked)
        self.__ui.video_player_push_button_video2_step_forward.clicked.connect(self.__cb_video2_step_forward)
        self.__ui.video_player_push_button_video2_step_reverse.clicked.connect(self.__cb_video2_step_reverse)
        self.__ui.slider_video['cam2'].setMinimum(1)
        self.__ui.slider_video['cam2'].valueChanged.connect(self.__cb_video2_slider_changed)
        self.__ui.video_player_push_button_video2_copy.clicked.connect(self.__cb_video2_copy_clicked)
        self.__ui.video_player_push_button_video2_find.clicked.connect(self.__cb_video2_find_clicked)

        ''' Video player callbacs and events '''
        event.on(VideoPlayer.EVENT_FRAME_NEW, self.__evt_videoplayer_play_new_frame)

    def __evt_videoplayer_play_new_frame(self, frame :Frame):
        self.display_frame(frame)
        ''' block signal on slider change since it will do a video_player.set_poistion on change
        and thereby intrduce a circular event '''
        self.__ui.slider_video[frame.get_cam()].blockSignals(True)
        self.__ui.slider_video[frame.get_cam()].setSliderPosition(frame.get_position())
        self.__ui.slider_video[frame.get_cam()].blockSignals(False)

        ''' Display time '''
        self.__ui.label_time_video[frame.get_cam()].setText(
            self.__win.format_time(
                self.__video_player.get_time(frame.get_cam())
            )
        )

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

    def video_display_frame_time(self, cam: str, time: int):
        self.__ui.label_time_video[cam].setText(
            self.__win.format_time(time)
        )

    def display_frame(self, frame :Frame):
        ''' display video frame '''
        image = frame.pop_image_load_if_missing(self.__globals.get_db(), self.__globals.get_game())

        # Draw center line
        cv.rectangle(image, (160, 0), (160, 480), (0, 0, 0), 1)
        # Draw ground level
        cv.rectangle(image, (0, self.__globals.get_ground_level()), (320, self.__globals.get_ground_level()), (0, 0, 0), 1)

        image_qt = QtGui.QImage(image, image.shape[1], image.shape[0], image.strides[0], QtGui.QImage.Format_Indexed8)
        self.__ui.widget_video[frame.get_cam()].setPixmap(QtGui.QPixmap.fromImage(image_qt))

    def enable_gui_elements(self, enabled: bool):
        self.__ui.video_player_slider_video1.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_find.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_play_reverse.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_step_reverse.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_stop.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_step_forward.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_play_forward.setEnabled(enabled)
        self.__ui.video_player_push_button_video1_copy.setEnabled(enabled)

        self.__ui.video_player_push_button_video2_play_reverse.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_step_reverse.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_stop.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_step_forward.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_play_forward.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_copy.setEnabled(enabled)
        self.__ui.video_player_push_button_video2_find.setEnabled(enabled)
        self.__ui.video_player_slider_video2.setEnabled(enabled)


