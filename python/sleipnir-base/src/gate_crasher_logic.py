import time
import logging
import typing

import event
from configuration import Configuration
from globals import Globals
from camera_server import CameraServer
from cameras_data import CamerasData
from frame import Frame
from errors import *
from motion_tracker import MotionTrackerDoMessage, MotionTrackerDoneMessage, MotionTrackerWorker
#from gate_crasher_announcements import Announcements, Announcement
#import database.gate_crasher_announcement_dao as announcement_dao
import database.frame_dao as frame_dao

logger = logging.getLogger(__name__)

'''
SpeedLogic emits the following events

GateCrasherLogic.EVENT_GATE_CRASHER_START                                            : Started gate crasher game
GateCrasherLogic.EVENT_GATE_CRASHER_STOP                                             : Stopped gate crasher game
GateCrasherLogic.EVENT_GATE_CRASHER_NEW_FRAME frame :Frame                           : A camera have a new frame
GateCrasherLogic.EVENT_GATE_CRASHER_HIT_GATE : GateCrasherGateAnnouncement           : A gate crasher game have restarted
GateCrasherLogic.EVENT_GATE_CRASHER_FINISH : int                                     : A gate crasher game have finnished
GateCrasherLogic.EVENT_GATE_CRASHER_RESTART                                          : A gate crasher game have restarted
'''

class GateCrasherState: 
    def __init__(self):        
        ''' collection of frames '''
        self.cameras_data = None    # type: CamerasData

        ''' GataCrasher running? '''
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

        ''' Gate you need to hit next '''
        self.current_gate_number = 0

        ''' GateCrasher Level 0 index based'''
        self.level = 0

        ''' timestamp when to restart due to be too slow '''
        self.pass_restart_time = None

        ''' timestamp when we hit first gate '''
        self.timestamp_start = None

        ''' timestamp when we hit first gate '''
        self.current_runtime_ms = 0

        ''' Current level index'''
        self.level = 0

        ''' Announcements '''
        self.announcements = [] # type: list[GateCrasherAnnouncement]



class GateCrasherHitPoint:
    def __init__(self, cam : str, direction: str):
        self.__cam = cam
        self.__direction = direction

    def get_cam(self):
        return self.__cam

    def get_direction(self):
        return self.__direction

class GateCrasherLevel():
    def __init__(self, name: str, hitpoints:  typing.List[GateCrasherHitPoint]):
        self.__name = name
        self.__hitpoints = hitpoints

    def get_name(self):
        return self.__name

    def get_hitpoint(self, gate_number: int) -> GateCrasherHitPoint:
        return self.__hitpoints[gate_number]

    def get_length(self):
        return len(self.__hitpoints)

class GateCrasherAnnouncement:
    def __init__(self, level_name, gate_number, cam, position, timestamp, direction, angle, altitude, time_ms):
        self.__level_name = level_name
        self.__gate_number = gate_number
        self.__cam = cam
        self.__position = position
        self.__timestamp = timestamp
        self.__direction = direction
        self.__angle = angle            # hit is above max dive (NOT IMPLEMENTED)
        self.__altitude = altitude      # LOW, HIGH (NOT IMPLEMENTED)
        self.time_ms = time_ms

    def get_level_name(self) -> str:
        return self.__level_name

    def get_gate_number(self) -> int:
        return self.__gate_number

    def get_cam(self) -> str:
        return self.__cam

    def get_position(self) -> int:
        return self.__position

    def get_timestamp(self) -> int:
        return self.__timestamp

    def get_direction(self) -> str:
        return self.__direction

    def get_time_ms(self) -> int:
        return self.time_ms

class GateCrasherLogic:
    EVENT_GATE_CRASHER_START           = 'gatecrasher.run.start'
    EVENT_GATE_CRASHER_STOP            = 'gatecrasher.run.stop'
    EVENT_GATE_CRASHER_NEW_FRAME       = 'gatecrasher.run.new_frame'
    EVENT_GATE_CRASHER_HIT_GATE        = 'gatecrasher.run.hitgate'
    EVENT_GATE_CRASHER_FINISH          = 'gatecrasher.run.finish'
    EVENT_GATE_CRASHER_RESTART         = 'gatecrasher.run.restart'
    EVENT_GATE_CRAHSER_HIT_NEW         = 'gatecrasher.run.hitnew'

    __MAX_ALLOWED_LAG = 15

    def __init__(self, globals: Globals, camera_server: CameraServer, configuration: Configuration):
        self.__globals = globals
        self.__state = GateCrasherState()
        self.__camera_server = camera_server

        self.__levels = [] # type: list[GateCrasherLevel]
        self.__init_levels()

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

        event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camerserver_camera_offline)
        event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

    def __evt_camerserver_camera_offline(self, cam):
        ''' Camera have gone offline '''
        self.stop_run()

    def __evt_globals_flight_change(self, flight):
        pass

    def get_current_runtime(self):
        return self.__state.current_runtime_ms

    def start_run(self):
        ''' Starting gate crasher '''
        logger.info("Gate Crasher starting...")

        ''' gate crasher already in progress? '''
        if self.__state.running: return

        if self.__camera_server.is_ready_to_shoot() == False:
            ''' Server is not online, we can't start '''
            raise IllegalStateError("Camera server is not ready to shoot")

        ''' Reset into a clean state '''
        self.__motion_tracker_threads['cam1'].reset()
        self.__motion_tracker_threads['cam2'].reset()
        self.__state.current_gate_number = 0
        self.__state.lag_recovery = 0
        self.__state.pass_restart_time = None
        self.announcements = []
        self.current_runtime_ms = 0

        try:
            logger.info("Deleting Frames for flight %d, hang on..." % self.__globals.get_flight())
            frame_dao.delete_flight(self.__globals.get_db(), self.__globals.GAME_GATE_CRASHER ,self.__globals.get_flight())
        except Exception as e:
            logger.error(str(e))
            return

        event.on(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.running = True

        self.__state.cameras_data = CamerasData(self.__globals.get_db(), self.__globals.get_game(), self.__globals.get_flight())
        self.__camera_server.start_shooting(self.__state.cameras_data)
        event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_START)

    def stop_run(self):
        ''' Stopping run '''
        logger.info("Gate Crasher stopping...")

        ''' Timed run not in progress? '''
        if self.__state.running == False: return

        ''' Stop the camera server '''
        self.__camera_server.stop_shooting()

        ''' Disable the new frame event '''
        event.off(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)

        self.__state.running = False
        event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_STOP)

    def __cameraserver_evt_new_frame(self, frame: Frame):
        ''' Make sure we do not process any lingering event, it would
        screw up the runtime '''
        if self.__state.running == False: return

        ''' See if we are in lag recovery mode '''
        if self.__state.lag_recovery > 0:
            self.__state.lag_recovery -= 1
            return

        ''' Gate crash timeout? '''
        if self.__state.pass_restart_time != None and time.time() > self.__state.pass_restart_time:
            self.__state.pass_restart_time = None
            event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_RESTART)
            return

        cam = frame.get_cam()

        ''' The last frame on this camera '''
        cameras_data_last_position = self.__state.cameras_data.get_last_frame(cam).get_position()

        ''' Check if we need to go into lag recovery mode '''
        if cameras_data_last_position - frame.get_position() > GateCrasherLogic.__MAX_ALLOWED_LAG:
            logger.warning("Lag detected when fetching new frame " + cam + ": " + str(frame.get_position()) + ", skipping ahead " + str(GateCrasherLogic.__MAX_ALLOWED_LAG) + " frames")
            ''' Enable the lag recovery for __MAX_ALLOWED_LAG * 3 frames 
            We tripple up since there are two cameras that are sending images 
            plus extra headroom '''
            self.__state.lag_recovery = GateCrasherLogic.__MAX_ALLOWED_LAG * 3
            return
                
        worker = self.__motion_tracker_threads[cam]

        ''' Wait for the motion tracker to finish before trying a new one '''
        worker.wait()
        done_message = worker.get_motion_tracker_done_message()

        ''' Set the current runtime, if we have hit first gate,
        since we don't want jitter oback and forth on this, we only use one cam.
        The finishing time will still get from the correct cam '''
        if self.__state.current_gate_number > 0 and cam == 'cam1':
            self.__state.current_runtime_ms = self.__state.cameras_data.get_frame(cam, done_message.get_position()).get_timestamp() - self.__state.timestamp_start

        do_message = MotionTrackerDoMessage(
            frame.pop_image_load_if_missing(self.__globals.get_db(), self.__globals.get_game()),
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

        ''' Note that we are emiting an old frame since we want to motion tracking
        information drawm '''
        event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_NEW_FRAME, frame)

        ''' Check motion '''
        if (done_message.have_motion()):
            self.check_run(cam, done_message)

    def check_run(self, cam, motion_tracker_done_message: MotionTrackerDoneMessage):
        ''' Check if we hit the gates in the correct order, and in the correct way '''

        hitpoint = self.__levels[self.__state.level].get_hitpoint(self.__state.current_gate_number)
        motion_tracker_direction_name = ['LEFT', 'RIGHT'][int((motion_tracker_done_message.get_direction() + 1) / 2)] # -1 == 0, 1 == 1

        motion_tracker_timestamp = self.__state.cameras_data.get_frame(cam, motion_tracker_done_message.get_position()).get_timestamp()

        if hitpoint.get_direction() == motion_tracker_direction_name and hitpoint.get_cam() == cam:

            ''' Calculate time '''
            if self.__state.current_gate_number == 0:
                time_ms = 0
                self.__state.timestamp_start = motion_tracker_timestamp
            else:
                time_ms = motion_tracker_timestamp - self.__state.announcements[self.__state.current_gate_number - 1].get_timestamp()

            ''' Create announcement '''
            announcement = GateCrasherAnnouncement(
                self.__levels[self.__state.level].get_name(),
                self.__state.current_gate_number,
                hitpoint.get_cam(),
                motion_tracker_done_message.get_position(),
                motion_tracker_timestamp,
                hitpoint.get_direction,
                '','',
                time_ms
            )
            self.__state.announcements.append(announcement)

            event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_HIT_GATE, announcement)


            if self.__state.current_gate_number == self.__levels[self.__state.level].get_length() - 1:
                ''' Reached the finish '''

                ''' Calculate exact finish time'''
                finish_time = 0.0
                for announcement in self.__state.announcements:
                    finish_time += announcement.get_time_ms()

                event.emit(GateCrasherLogic.EVENT_GATE_CRASHER_FINISH, finish_time)
                self.stop_run()
                return

            ''' Move on to next gate '''
            self.__state.current_gate_number += 1

    def get_time(self, frame: Frame) -> int:
        ''' Has run started '''
        if self.__state.timestamp_start is None: return 0

        ''' get time on frame position since run start '''
        t = frame.get_timestamp() - self.__state.timestamp_start
        if t < 0: t =0
        return t

    def __init_levels(self):
        self.__levels.clear()
        self.__levels.append(GateCrasherLevel("Beginner 1",
            [
                GateCrasherHitPoint('cam1', 'RIGHT'),
                GateCrasherHitPoint('cam2', 'RIGHT'),
                GateCrasherHitPoint('cam1', 'LEFT' ),
                GateCrasherHitPoint('cam2', 'RIGHT')
            ])
        )
        
        self.__levels.append(GateCrasherLevel("Beginner 2",
            [
                GateCrasherHitPoint('cam1', 'RIGHT'),
                GateCrasherHitPoint('cam2', 'RIGHT'),
                GateCrasherHitPoint('cam1', 'LEFT' ),
                GateCrasherHitPoint('cam2', 'RIGHT')
            ])
        )

        self.__levels.append(GateCrasherLevel("Beginner 3",
            [
                GateCrasherHitPoint('cam1', 'RIGHT'),
                GateCrasherHitPoint('cam2', 'RIGHT'),
                GateCrasherHitPoint('cam1', 'LEFT' ),
                GateCrasherHitPoint('cam2', 'RIGHT')
            ])
        )
