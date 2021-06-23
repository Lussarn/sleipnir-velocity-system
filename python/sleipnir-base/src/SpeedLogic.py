import logging

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import QTimer, QThread

import Event
from Configuration import Configuration
from Globals import Globals
from CameraServer import CameraServer
from CamerasData import CamerasData
from Frame import Frame
from Errors import *
from MotionTracker import MotionTracker, MotionTrackerDoMessage, MotionTrackerDoneMessage
import time

logger = logging.getLogger(__name__)

'''
SpeedLogic emits the following events

SpeedLogic.EVENT_SPEED_START                        : Start timed run camera
SpeedLogic.EVENT_SPEED_STOP                         : Stop timed run camera
SpeedLogic.EVENT_SPEED_NEW_FRAME frame :Frame       : A camera have a new frame
'''

class SpeedState: 
    def __init__(self):        
        ''' collection of frames '''
        self.cameras_data = None    # type: CamerasData

        ''' SpeedLogic running? '''
        self.running = False        # type: bool

        self.cameras_data           # type: CamerasData

        ''' Max angle of aircraft a motion track will register '''
        self.max_dive_angle = 0
        ''' blur strengh when motion tracking '''
        self.blur_strength = 0

        ''' If lag_recovery > 0 do noting when a new frames
        arrives on __cameraserver_evt_new_frame to let the system
        recover. decrease lag_recovery by one in this case so
        it will eventually be zero again '''
        self.lag_recovery = 0

class SpeedLogic:
    EVENT_SPEED_START           = "speedlogic.speed.start"
    EVENT_SPEED_STOP            = "speedlogic.speed.stop"
    EVENT_SPEED_NEW_FRAME       = "speedlogic.speed.new_frame"

    __MAX_ALLOWED_LAG = 15

    def __init__(self, globals: Globals, camera_server: CameraServer, configuration: Configuration):
        self.__globals = globals
        self.__state = SpeedState()
        self.__camera_server = camera_server

        ''' read from configuration '''
        self.__state.max_dive_angle = configuration.get_max_dive_angle()
        logger.info("Max dive angle is set at " + str(self.__state.max_dive_angle) + "°")
        self.__state.blur_strength = configuration.get_blur_strength()
        logger.info("Blur strength is set at t at " + str(self.__state.blur_strength))

        ''' setup motion tracker threads '''
        self.__motion_tracker_threads = {
            'cam1': MotionTrackerWorker('cam1'),
            'cam2': MotionTrackerWorker('cam2')
        }

        ''' setup motion trackers '''
        self.__motion_trackers = {
            'cam1': MotionTracker(),
            'cam2': MotionTracker()
        }

        Event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camerserver_camera_offline)
        
    def __evt_camerserver_camera_offline(self, cam):
        ''' Camera have gone offline '''
        self.stop_run()

    def start_run(self):
        ''' Starting run '''

        ''' Timed run already in progress? '''
        if self.__state.running: return

        if self.__camera_server.is_ready_to_shoot() == False:
            ''' Server is not online, we can't start '''
            raise IllegalStateError("Camera server is not ready to shoot")

        Event.on(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.running = True

        self.__motion_tracker_threads['cam1'].reset()
        self.__motion_tracker_threads['cam2'].reset()

        self.__state.cameras_data = CamerasData(self.__globals.get_db(), self.__globals.get_flight())
        self.__camera_server.start_shooting(
            self.__globals.get_flight(),
            self.__state.cameras_data
        )
        Event.emit(SpeedLogic.EVENT_SPEED_START)

    def stop_run(self):
        ''' Stopping run '''

        ''' Timed run not in progress? '''
        if self.__state.running == False: return

        ''' Stop the camera server '''
        self.__camera_server.stop_shooting()

        Event.off(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.running = False
        Event.emit(SpeedLogic.EVENT_SPEED_STOP)

    def __cameraserver_evt_new_frame(self, frame: Frame):
        ''' See if we are in lag recovery mode '''
        if self.__state.lag_recovery > 0:
            self.__state.lag_recovery -= 1
            return

        cam = frame.get_cam()

        ''' The last frame on this camera '''
        cameras_data_last_position = self.__state.cameras_data.get_last_frame(cam).get_position()

        ''' Check if we need to go into lag recovery mode '''
        if cameras_data_last_position - frame.get_position() > SpeedLogic.__MAX_ALLOWED_LAG:
            logger.warning("Lag detected when fetching new frame " + cam + ": " + str(frame.get_position()) + ", skipping ahead " + str(SpeedLogic.__MAX_ALLOWED_LAG) + " frames")
            ''' Enable the lag recovery for __MAX_ALLOWED_LAG * 2 frames 
            We double up since there are two cameras that are sending images '''
            self.__state.lag_recovery = SpeedLogic.__MAX_ALLOWED_LAG * 2
            return
                
        worker = self.__motion_tracker_threads[cam]

        ''' Wait for the motion tracker to finnish before trying a new one '''
        worker.wait()
        done_message = worker.get_motion_tracker_done_message()
        
        do_message = MotionTrackerDoMessage(
            frame.pop_image_load_if_missing(self.__globals.get_db()),
            frame.get_position(),
            self.__globals.get_ground_level(), 
            self.__state.max_dive_angle,
            self.__state.blur_strength)
        worker.do_motion_tracking(do_message)

        try:
            frame = self.__state.cameras_data.get_frame(cam, done_message.get_position())
        except IndexError:
            ''' This happens when reaching this the first time after reset 
            because we fetch a done_messsage which hasn't been processed '''
            return

        frame.set_image(done_message.get_image())
        if (done_message.have_motion()):
            print ("have motion")

        Event.emit(SpeedLogic.EVENT_SPEED_NEW_FRAME, frame)

    def get_time(self, frame: Frame) -> int:
        ''' get time on frame position '''
        t = frame.get_timestamp() - self.__state.cameras_data.get_start_timestamp()
        if t < 0: t =0
        return t

    def get_next_frame_allow_lag(self, cam: str) -> Frame:
        ''' Get the next Frame from cameras_data, return None if no new is available '''

        ''' The last frame on this camera '''
        cameras_data_last_position = self.__state.cameras_data.get_last_frame(cam).get_position()

        ''' See if we have a new frame, return None if not '''
        if cameras_data_last_position >= self.__state.last_served_position[cam]: return None

        ''' We only add a frame if we are below thre last frame on the camera '''
        self.__state.last_served_position[cam] += 1

        ''' lag detection '''
        if cameras_data_last_position - self.__state.last_served_position[cam] > SpeedLogic.__MAX_ALLOWED_LAG:
            logger.warning("Lag detected when fetching new frame " + cam + ": " + str(self.__state.last_served_position[cam]) + ", skipping ahead " + str(SpeedLogic.__MAX_ALLOWED_LAG) + " frames")
            self.__state.last_served_position[cam] = cameras_data_last_position

        return self.__state.cameras_data.get_frame(cam, self.__state.last_served_position[cam]) 

''' Worker thread doing the actual motion tracking '''
class MotionTrackerWorker(QThread):
    def __init__(self, cam: str):
        # "cam1" or "cam2"
        self.__cam = cam

        ''' The Motion tracker '''
        self.__motion_tracker = MotionTracker()

        ''' Message to pass into motion tracker '''
        self.__motion_tracker_do_message = None

        ''' Message to transfer back to the program '''
        self.__motion_tracker_done_message = MotionTrackerDoneMessage(None, 0, 0)

        QThread.__init__(self)
        self.setObjectName("MotionTrack-" + self.__cam + "-QThread")

    def reset(self):
        self.wait()
        self.__motion_tracker.reset()

    def get_motion_tracker_done_message(self):
        return self.__motion_tracker_done_message

    def do_motion_tracking(self, motion_tracker_do_message: MotionTrackerDoMessage):
        self.__motion_tracker_do_message = motion_tracker_do_message
        self.start()

    def run(self):
        self.__motion_tracker_done_message = self.__motion_tracker.motion_track(self.__cam, self.__motion_tracker_do_message)
    