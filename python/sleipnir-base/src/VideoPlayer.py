import logging
import time

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import QTimer

import Event
from Globals import Globals
from Frame import Frame
from CamerasData import CamerasData
from Configuration import Configuration


from MotionTracker import MotionTracker, MotionTrackerDoMessage

logger = logging.getLogger(__name__)

'''
VideoPlayer emits the following events

VideoPlayer.EVENT_PLAY_START cam: str               : Start playing video
VideoPlayer.EVENT_PLAY_STOP  cam: str               : Stop playing video
VideoPlayer.EVENT_FRAME_NEW  frame: Frame           : A new frame have arived
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
    EVENT_FRAME_NEW            = "videoplayer.frame.new"

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
        ''' Stop both timers '''
        self.__timer_play.stop()
        self.__timer_find.stop()

    def __evt_globals_flight_change(self, flight):
        ''' When flights change load new cameras_datas '''
        self.__stop_timers()
        self.__state.cameras_data = CamerasData(self.__globals.get_db(), flight)
        for cam in ['cam1', 'cam2']:
            self.__state.position[cam] = 1
            self.__state.direction[cam] = VideoPlayer.DIRECTION_FORWARD
            self.__state.play[cam] = VideoPlayer.PLAY_STOPPED
        self.__state.start_timestamp = self.__state.cameras_data.get_start_timestamp()

    def __cb_timer_play(self):
        ''' Play Video at normal speed, runs on self.__timer_play '''
        for cam in ['cam1', 'cam2']:
            if self.__state.play[cam] == VideoPlayer.PLAY_NORMAL:
                if (self.__state.direction[cam] == VideoPlayer.DIRECTION_FORWARD):
                    ''' Play forward '''
                    self.__state.position[cam] += 1
                    if self.__state.cameras_data.get_last_frame(cam) is None or self.__state.position[cam] >= self.__state.cameras_data.get_last_frame(cam).get_position():
                        self.stop(cam)
                        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                        Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)
                        continue
                else:
                    ''' Play reverse '''
                    self.__state.position[cam] -= 1
                    if self.__state.position[cam] == 0:
                        self.__state.position[cam] = 1
                        self.stop(cam)
                        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                        Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)
                        continue
                
                frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)

    def __cb_timer_find(self):
        ''' Find motion at full speed, runs on self.__timer_find '''
        for cam in ['cam1', 'cam2']:
            if self.__state.play[cam] == VideoPlayer.PLAY_FIND:
                ''' Finding '''
                self.__state.position[cam] += 1
                if self.__state.cameras_data.get_last_frame(cam) is None or self.__state.position[cam] >= self.__state.cameras_data.get_last_frame(cam).get_position():
                    self.stop(cam)
                    frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
                    Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)
                    continue
                frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])

                do_message = MotionTrackerDoMessage(
                    frame.pop_image_load_if_missing(self.__globals.get_db()),
                    frame.get_position(),
                    self.__globals.get_ground_level(), 
                    self.__state.max_dive_angle, 
                    self.__state.blur_strength)
                done_message = self.__motion_trackers[cam].motion_track(cam, do_message)
                if done_message.have_motion():
                    self.stop(cam)

                frame.set_image(done_message.get_image())
                Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)
       
    def __update_timer_running(self):
        ''' Enable and disable the timers according to the __state.play '''

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
        ''' Play from current position in either direction '''
        if (self.__state.play[cam] == VideoPlayer.PLAY_NORMAL and self.__state.direction[cam] == direction): return
        self.__state.direction[cam] = direction
        self.__state.play[cam] = VideoPlayer.PLAY_NORMAL
        self.__update_timer_running()
        Event.emit(VideoPlayer.EVENT_PLAY_START, cam)

    def find(self, cam: str):
        ''' Find from current position '''
        if (self.__state.play[cam] == VideoPlayer.PLAY_FIND): return
        self.__motion_trackers[cam].set_position(self.__state.position[cam])
        self.__state.direction[cam] = VideoPlayer.DIRECTION_FORWARD
        self.__state.play[cam] = VideoPlayer.PLAY_FIND
        self.__update_timer_running()

    def stop_all(self):
        ''' Stop both videos if they are running '''
        self.stop('cam1')
        self.stop('cam2')

    def stop(self, cam: str):
        ''' Stop video '''
        if (self.__state.play[cam] == VideoPlayer.PLAY_STOPPED): return
        self.__state.play[cam] = VideoPlayer.PLAY_STOPPED
        self.__update_timer_running()
        Event.emit(VideoPlayer.EVENT_PLAY_STOP, cam)

    def step(self, cam: str, direction: int):
        ''' Step one frame in either direction '''
        self.stop(cam)

        if direction == VideoPlayer.DIRECTION_REVERSE:
            if self.__state.position[cam] == 1: return
            self.__state.position[cam] -= 1
        else:
            if self.__state.position[cam] == self.__state.cameras_data.get_last_frame(cam).get_position(): return
            self.__state.position[cam] += 1

        frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
        Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)

    def copy(self, source_cam: str, dest_cam: str):
        ''' Copy video the the other side based on timestamp '''
        self.stop_all()
        timestamp_source = self.__state.cameras_data.get_frame(source_cam, self.__state.position[source_cam]).get_timestamp()

        ''' Start at beginning of dest and move until timestamp is bigger than source '''
        for i in range(1, self.__state.cameras_data.get_last_frame(dest_cam).get_position() + 1):
            timestamp_dest = self.__state.cameras_data.get_frame(dest_cam, i).get_timestamp()
            if timestamp_dest >= timestamp_source:
                break
        self.__state.position[dest_cam] = i

        frame = self.__state.cameras_data.get_frame(dest_cam, self.__state.position[dest_cam])
        Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)

    def get_current_frame(self, cam) -> Frame:
        ''' Get frame on current position '''
        return self.__state.cameras_data.get_frame(cam, self.__state.position[cam])

    def set_position(self, cam: str, position: int):
        ''' Set current position '''
        if position < 1: raise IndexError("position out of range")
        self.__state.position[cam] = position
        try:
            frame = self.__state.cameras_data.get_frame(cam, self.__state.position[cam])
        except IndexError:
            return
        Event.emit(VideoPlayer.EVENT_FRAME_NEW, frame)

    def get_time(self, cam: str):
        ''' get time on current position '''
        t = self.__state.cameras_data.get_frame(cam, self.__state.position[cam]).get_timestamp() - self.__state.start_timestamp
        if t < 0: t =0
        return t

    def get_last_frame(self, cam: str):
        ''' Get last frame of video '''
        return self.__state.cameras_data.get_last_frame(cam)

    def get_frame(self, cam: str, position: int) -> Frame:
        return self.__state.cameras_data.get_frame(cam, position)
