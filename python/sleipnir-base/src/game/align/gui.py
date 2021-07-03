
from globals import Globals
import event
from errors import *
from ui_sleipnir_window import Ui_SleipnirWindow
from camera_server import CameraServer
from video_player.video_player_gui import VideoPlayerGUI
from frame.frame import Frame

from game.align.logic import Logic
from game.align.events import *

import logging

logger = logging.getLogger(__name__)

class GUI:
    def __init__(self, win):
        from sleipnir import SleipnirWindow
        self.__win = win                                        # type: SleipnirWindow
        self.__ui = win.get_ui()                                # type: Ui_SleipnirWindow
        self.__globals = win.get_globals()                      # type: Globals
        self.__camera_server = win.get_camera_server()          # type: CameraServer
        self.__video_player_gui = win.get_video_player_gui()    # type: VideoPlayerGUI

        self.__logic = Logic(self.__globals, self.__camera_server)

        event.on(EVENT_ALIGN_START, self.__evt_align_start)
        event.on(EVENT_ALIGN_STOP, self.__evt_align_stop)
        event.on(EVENT_ALIGN_FRAME_NEW, self.__evt_align_frame_new)

    def __evt_align_start(self, cam):
        self.__win.enable_all_gui_elements(False)
        if cam == 'cam1':
            self.__ui.align_push_button_video1.setText('Stop')
            self.__ui.align_push_button_video2.setEnabled(False)
        else:
            self.__ui.align_push_button_video2.setText('Stop')
            self.__ui.align_push_button_video1.setEnabled(False)

    def __evt_align_stop(self, cam):
        self.__win.enable_all_gui_elements(True)

        self.__ui.align_push_button_video1.setText('Align')
        self.__ui.align_push_button_video2.setText('Align')
        
        if self.__camera_server.is_online('cam1'): 
            self.__ui.align_push_button_video1.setEnabled(True)
        if self.__camera_server.is_online('cam2'): 
            self.__ui.align_push_button_video2.setEnabled(True)

        ''' Check status for start stop buttons '''
        self.__ui.sleipnir_push_button_stop.setEnabled(False)
        if not self.__camera_server.is_ready_to_shoot():
            self.__ui.sleipnir_push_button_start.setEnabled(False)


    def __evt_align_frame_new(self, frame :Frame):
        self.__video_player_gui.display_frame(frame, frame.get_cam())        