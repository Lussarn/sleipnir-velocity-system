import logging
import time

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import QTimer

import Event
from Globals import Globals
from database.DB import DB
from Frame import Frame
from CameraServer import CameraServer
from CamerasData import CamerasData
from Configuration import Configuration


from MotionTracker import MotionTracker, MotionTrackerDoMessage, MotionTrackerDoneMessage

logger = logging.getLogger(__name__)

'''
VideoPlayer emits the following events

VideoPlayer.EVENT_PLAY_START cam :str               : Start playing video
VideoPlayer.EVENT_PLAY_STOP  cam :str               : Stop playing video
VideoPlayer.EVENT_PLAY_NEW_FRAME frame :Frame       : A new frame have arived
'''

class VideoPlayerState:
    def __init__(self):
        self.position = {
            'cam1': 1,
            'cam2': 1
        }

        self.direction = {
            'cam1': VideoPlayer.DIRECTION_FORWARD,
            'cam2': VideoPlayer.DIRECTION_FORWARD
        }

        self.play = {
            'cam1': VideoPlayer.PLAY_STOPPED,
            'cam2': VideoPlayer.PLAY_STOPPED
        }

        ''' frame collection '''
        self.cameras_data = None        # type: CamerasData
        ''' first timestamp in frames collection '''
        self.start_timestamp = None

        ''' Max angle of aircraft a motion track will register '''
        self.max_dive_angle = 0
        ''' blur strengh when motion tracking '''
        self.blur_strength = 0


class VideoPlayer:
    DIRECTION_FORWARD = 1
    DIRECTION_REVERSE = -1

    PLAY_STOPPED = 0
    PLAY_NORMAL  = 1
    PLAY_FIND    = 2

    EVENT_PLAY_START           = "videoplayer.play.start"
    EVENT_PLAY_STOP            = "videoplayer.play.stop"
    EVENT_PLAY_NEW_FRAME       = "videoplayer.play.new_frame"

    def __init__(self, globals: Globals, qwidget: QWidget, configuration: Configuration):
        self.__state = VideoPlayerState()
        self.__globals = globals

        ''' read from configuration '''
        self.__state.max_dive_angle = configuration.get_max_dive_angle()
        logger.info("Max dive angle is set at " + str(self.__state.max_dive_angle) + "°")
        self.__state.blur_strength = configuration.get_blur_strength()
        logger.info("Blur strength is set at t at " + str(self.__state.blur_strength))

        ''' setup motion trackers '''
        self.__motion_trackers = {
            'cam1': MotionTracker(),
            'cam2': MotionTracker()
        }

        ''' flight change event '''
        Event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

        ''' Setup timer for play '''
        self.__timer_play = QTimer(qwidget)
        self.__timer_play.timeout.connect(self.__cb_timer_play)
        ''' Setup timer for find '''
        self.__timer_find = QTimer(qwidget)
        self.__timer_find.timeout.connect(self.__cb_timer_find)
        self.__evt_globals_flight_change(self.__globals.get_flight())

    def __stop_timers(self):
        self.__timer_play.stop()
        self.__timer_find.stop()

    def __evt_globals_flight_change(self, flight):
        print("FLIGHT CHANGE IN VIDEO_PLAYER")
        self.__stop_timers()
        self.__state.cameras_data = CamerasData(self.__globals.get_db(), flight)
        for cam in ['cam1', 'cam2']:
            self.__state.position[cam] = 1
            self.__state.direction[cam] = VideoPlayer.DIRECTION_FORWARD
            self.__state.play[cam] = VideoPlayer.PLAY_STOPPED
        self.__state.start_timestamp = self.__state.cameras_data.get_start_timestamp()

    def get_current_frame(self, cam):
        return self.__state.cameras_data.get_frame(cam, self.__state.position[cam])

    def __cb_timer_play(self):
        for cam in ['cam1', 'cam2']:
            if self.__state.play[cam] == VideoPlayer.PLAY_NORMAL:
                if (self.__state.direction[cam] == VideoPlayer.DIRECTION_FORWARD):
                    ''' Play forward '''
                    self.__state.position[cam] += 1
                    if self.__state.cameras_data.get_last_frame(cam) is None or self.__state.position[cam] >= self.__state.cameras_data.get_last_frame(cam).get_position():
                        self.stop(cam)
                        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                        Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)
                        continue
                else:
                    ''' Play reverse '''
                    self.__state.position[cam] -= 1
                    if self.__state.position[cam] == 0:
                        self.__state.position[cam] = 1
                        self.stop(cam)
                        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                        Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)
                        continue

                frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)

    def __cb_timer_find(self):
        for cam in ['cam1', 'cam2']:
            if self.__state.play[cam] == VideoPlayer.PLAY_FIND:
                ''' Finding '''
                self.__state.position[cam] += 1
                if self.__state.cameras_data.get_last_frame(cam) is None or self.__state.position[cam] >= self.__state.cameras_data.get_last_frame(cam).get_position():
                    self.stop(cam)
                    frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                    Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)
                    continue
        
                frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])

                do_message = MotionTrackerDoMessage(
                    frame.get_image_load_if_missing(self.__globals.get_db()),
                    frame.get_position(),
                    self.__globals.get_ground_level(), 
                    self.__state.max_dive_angle, 
                    self.__state.blur_strength)
                done_message = self.__motion_trackers[cam].motion_track(cam, do_message)
                if done_message.have_motion():
                    self.stop(cam)

                Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)
       

    def __update_timer_running(self):
        ''' The play timer should run if any of the videos are playing '''
        if (self.__state.play['cam1'] == VideoPlayer.PLAY_NORMAL or self.__state.play['cam2'] == VideoPlayer.PLAY_NORMAL):
            ''' 11 Is an aproximatin to get correct framerate since 
                we have 90 fps material, it's not uber important '''
            self.__timer_play.start(11)
        else:
            self.__timer_play.stop()           

        ''' The find timer should run if any of the videos are finding '''
        if (self.__state.play['cam1'] == VideoPlayer.PLAY_FIND or self.__state.play['cam2'] == VideoPlayer.PLAY_FIND):
            ''' Full speed when finding '''
            self.__timer_find.start(0)
        else:
            self.__timer_find.stop()           

    def play(self, cam: str, direction: int):
        if (self.__state.play[cam] == VideoPlayer.PLAY_NORMAL and self.__state.direction[cam] == direction): return
        self.__state.direction[cam] = direction
        self.__state.play[cam] = VideoPlayer.PLAY_NORMAL
        self.__update_timer_running()
        Event.emit(VideoPlayer.EVENT_PLAY_START, cam)

    def find(self, cam: str):
        if (self.__state.play[cam] == VideoPlayer.PLAY_FIND): return
        self.__motion_trackers[cam].set_position(self.__state.position[cam])
        self.__state.direction[cam] = VideoPlayer.DIRECTION_FORWARD
        self.__state.play[cam] = VideoPlayer.PLAY_FIND
        self.__update_timer_running()

    def stop(self, cam: str):
        if (self.__state.play[cam] == VideoPlayer.PLAY_STOPPED): return
        self.__state.play[cam] = VideoPlayer.PLAY_STOPPED
        self.__update_timer_running()
        Event.emit(VideoPlayer.EVENT_PLAY_STOP, cam)

    def step(self, cam: str, direction: int):
        self.stop(cam)

        if direction == VideoPlayer.DIRECTION_REVERSE:
            if self.__state.position[cam] == 1: return
            self.__state.position[cam] -= 1
        else:
            if self.__state.position[cam] == self.__state.cameras_data.get_last_frame(cam).get_position(): return
            self.__state.position[cam] += 1

        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
        Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)

    def copy(self, source_cam: str, dest_cam: str):
        self.stop('cam1')
        self.stop('cam2')
        timestamp_source = self.__state.cameras_data.get_frame(source_cam, self.__state.position[source_cam]).get_timestamp()

        ''' Start at beginning of dest and move until timestamp is bigger than source '''
        for i in range(1, self.__state.cameras_data.get_last_frame(dest_cam).get_position() + 1):
            timestamp_dest = self.__state.cameras_data.get_frame(dest_cam, i).get_timestamp()
            if timestamp_dest >= timestamp_source:
                break
        self.__state.position[dest_cam] = i

        frame = self.__state.cameras_data.get_frame(dest_cam, self.__state.position[dest_cam])
        Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)

    def set_position(self, cam: str, value: int):
        self.__state.position[cam] = value
        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
        Event.emit(VideoPlayer.EVENT_PLAY_NEW_FRAME, frame)

    def get_time(self, cam: str):
        print( self.__state.position[cam])
        t = self.__state.cameras_data.get_frame(cam, self.__state.position[cam]).get_timestamp() - self.__state.start_timestamp
        if t < 0: t =0
        return t

    def get_last_frame(self, cam: str):
        self.__state.cameras_data.get_last_frame(cam)