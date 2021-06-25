import time
import logging

import event
from configuration import Configuration
from globals import Globals
from camera_server import CameraServer
from cameras_data import CamerasData
from frame import Frame
from errors import *
from motion_tracker import MotionTrackerDoMessage, MotionTrackerDoneMessage, MotionTrackerWorker
from announcements import Announcements, Announcement
import database.announcement_dao as announcement_dao

logger = logging.getLogger(__name__)

'''
SpeedLogic emits the following events

SpeedLogic.EVENT_SPEED_START                        : Start timed run camera
SpeedLogic.EVENT_SPEED_STOP                         : Stop timed run camera
SpeedLogic.EVENT_SPEED_NEW_FRAME frame :Frame       : A camera have a new frame
SpeedLogic.EVENT_PASS_START : str                   : A speed pass have started on cam
SpeedLogic.EVENT_PASS_END : SpeedPassMessage        : A speed pass have ended
SpeedLogic.EVENT_PASS_ABORT :                       : A speed pass have been aborted
SpeedLogic.EVENT_ANNOUNCEMENT_NEW : Announcement    : An announcement has been added
SpeedLogic.EVENT_ANNOUNCEMENT_LOAD : Announcements  : announcemnet loaded
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

        ''' When the first camera triggers for a correct speed pass,
        either RIGHT on cam1 (flying from left) 
        or LEFT on cam2 (flying from right)
        pass_direction is set to either RIGHT or LEFT.
        It is used both for know if the right camerera is passed later,
        but also for discarding triggers on the wrong camera.
         '''
        self.pass_direction = None

        ''' position when the camera triggered for a pass '''
        self.pass_position = {
            'cam1': 0,
            'cam2': 0
        }

        ''' timestamp when to abort pass if not completed '''
        self.pass_abort_time = None

        ''' Distance between cameras in meters '''
        self.distance = None

        ''' Announcements '''
        self.announcements = Announcements()


class SpeedPassMessage:
    def __init__(self, direction: str, position_start: int, timestamp_start: int, position_end: int, timestamp_end: int):
        self.direction = direction
        self.position_start = position_start
        self.timestamp_start = timestamp_start
        self.position_end = position_end
        self.timestamp_end = timestamp_end

class SpeedLogic:
    EVENT_SPEED_START           = 'speedlogic.speed.start'
    EVENT_SPEED_STOP            = 'speedlogic.speed.stop'
    EVENT_SPEED_NEW_FRAME       = 'speedlogic.speed.new_frame'
    EVENT_PASS_START            = 'speedlogic.pass.start'
    EVENT_PASS_END              = 'speedlogic.pass.end'
    EVENT_PASS_ABORT            = 'speedlogic.pass.abort'
    EVENT_ANNOUNCEMENT_NEW      = 'speedlogic.announcement.new'
    EVENT_ANNOUNCEMENT_LOAD     = 'speedlogic.announcement.load'

    __MAX_ALLOWED_LAG = 15

    def __init__(self, globals: Globals, camera_server: CameraServer, configuration: Configuration):
        self.__globals = globals
        self.__state = SpeedState()
        self.__state.distance = 100
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

        event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camerserver_camera_offline)
        event.on(Globals.EVENT_FLIGHT_CHANGE, self.__evt_globals_flight_change)

    def __evt_camerserver_camera_offline(self, cam):
        ''' Camera have gone offline '''
        self.stop_run()

    def __evt_globals_flight_change(self, flight):
        ''' Loading announcement '''
        logger.info("Loading announcements for flight %d" % flight)
        self.__state.announcements = announcement_dao.fetch(self.__globals.get_db(), flight)
        event.emit(SpeedLogic.EVENT_ANNOUNCEMENT_LOAD, self.__state.announcements)

    def start_run(self):
        ''' Starting run '''

        ''' Timed run already in progress? '''
        if self.__state.running: return

        if self.__camera_server.is_ready_to_shoot() == False:
            ''' Server is not online, we can't start '''
            raise IllegalStateError("Camera server is not ready to shoot")

        ''' Reset into a clean state '''
        self.__motion_tracker_threads['cam1'].reset()
        self.__motion_tracker_threads['cam2'].reset()
        self.__state.pass_direction = None
        self.__state.lag_recovery = 0
        self.__state.pass_abort_time = None
        self.__state.announcements.clear()

        event.on(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.running = True

        self.__state.cameras_data = CamerasData(self.__globals.get_db(), self.__globals.get_flight())
        self.__camera_server.start_shooting(
            self.__globals.get_flight(),
            self.__state.cameras_data
        )
        event.emit(SpeedLogic.EVENT_SPEED_START)

    def stop_run(self):
        ''' Stopping run '''

        ''' Timed run not in progress? '''
        if self.__state.running == False: return

        ''' Stop the camera server '''
        self.__camera_server.stop_shooting()

        ''' Disable the new frame event '''
        event.off(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)

        ''' Save the announcements '''
        logger.info("Saving %d announcements" % self.__state.announcements.count())
        announcement_dao.store(self.__globals.get_db(), self.__globals.get_flight(), self.__state.announcements)

        self.__state.running = False
        event.emit(SpeedLogic.EVENT_SPEED_STOP)

    def __cameraserver_evt_new_frame(self, frame: Frame):
        ''' See if we are in lag recovery mode '''
        if self.__state.lag_recovery > 0:
            self.__state.lag_recovery -= 1
            return

        ''' Speed pass timeout? '''
        if self.__state.pass_abort_time != None and time.time() > self.__state.pass_abort_time:
            self.__state.pass_abort_time = None
            event.emit(SpeedLogic.EVENT_PASS_ABORT)

        cam = frame.get_cam()

        ''' The last frame on this camera '''
        cameras_data_last_position = self.__state.cameras_data.get_last_frame(cam).get_position()

        ''' Check if we need to go into lag recovery mode '''
        if cameras_data_last_position - frame.get_position() > SpeedLogic.__MAX_ALLOWED_LAG:
            logger.warning("Lag detected when fetching new frame " + cam + ": " + str(frame.get_position()) + ", skipping ahead " + str(SpeedLogic.__MAX_ALLOWED_LAG) + " frames")
            ''' Enable the lag recovery for __MAX_ALLOWED_LAG * 3 frames 
            We tripple up since there are two cameras that are sending images 
            plus extra headroom '''
            self.__state.lag_recovery = SpeedLogic.__MAX_ALLOWED_LAG * 3
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
            self.check_run(cam, done_message)

        ''' Note that we are emiting an old frame since we want to motion tracking
        information drawm '''
        event.emit(SpeedLogic.EVENT_SPEED_NEW_FRAME, frame)

    def check_run(self, cam: str, motion_tracker_done_message: MotionTrackerDoneMessage):
        ''' Discard hits that are obviously wrong '''

        if cam == 'cam1' and self.__state.pass_direction == None and motion_tracker_done_message.get_direction() == -1:
            # Camera 1 triggered LEFT run without being on a timed run, discard
            logger.info('Camera 1 triggered the wrong way for start of speed pass, discarding')
            return
        if cam == 'cam2' and self.__state.pass_direction == None and motion_tracker_done_message.get_direction() == 1:
            # Camera 1 triggered RIGHT run without being on a timed run, discard
            logger.info('Camera 2 triggered the wrong way for start of speed pass, discarding')
            return
        if cam == 'cam1' and self.__state.pass_direction == 'LEFT' and motion_tracker_done_message.get_direction() == 1:
            # Camera 1 (correct camera) triggered the wrong way, discard
            logger.info('Camera 1 triggered the wrong way in speed pass, discarding')
            return
        if cam == 'cam2' and self.__state.pass_direction == 'RIGHT' and motion_tracker_done_message.get_direction() == -1:
            # Camera 2 (correct camera) triggered the wrong way, discard
            logger.info('Camera 2 triggered the wrong way in speed pass, discarding')
            return

        ''' Check for start of RIGHT pass from camera 1 '''
        if cam == 'cam1' and self.__state.pass_direction == None and motion_tracker_done_message.get_direction() == 1:
            ''' Starting pass from cam1 '''
            self.__state.pass_position['cam1'] = motion_tracker_done_message.get_position()
            self.__state.pass_position['cam2'] == 0
            self.__state.pass_direction = 'RIGHT'
            ''' Max 6 second run '''
            self.__state.pass_abort_time = time.time() + 6.0
            logger.info("Initiating time run from cam 1 -->")
            event.emit(SpeedLogic.EVENT_PASS_START, cam)

        ''' Check for end of RIGHT pass on camera 2 '''
        if cam == 'cam2' and self.__state.pass_direction == 'RIGHT' and motion_tracker_done_message.get_direction() == 1:
            ''' Ending run on Cam 2 '''
            self.__state.pass_position['cam2'] = motion_tracker_done_message.get_position()
            self.__state.pass_direction = None
            logger.info("Timed run completed on cam 2 -->")
            ''' Clear the abort time since the pass is complete '''
            self.__state.pass_abort_time = None

            speed_pass_message = SpeedPassMessage(
                'RIGHT',
                self.__state.pass_position['cam1'],
                self.__state.cameras_data.get_frame('cam1', self.__state.pass_position['cam1']).get_timestamp(),
                self.__state.pass_position['cam2'],
                self.__state.cameras_data.get_frame('cam2', self.__state.pass_position['cam2']).get_timestamp(),                
            )
            event.emit(SpeedLogic.EVENT_PASS_END, speed_pass_message)
            self.__check_announcement(speed_pass_message)

        ''' Check for start of LEFT pass from camera 2 '''
        if cam == 'cam2' and  self.__state.pass_direction == None and motion_tracker_done_message.get_direction() == -1:
            ''' Starting pass from cam 2 '''
            self.__state.pass_position['cam2'] = motion_tracker_done_message.get_position()
            self.__state.pass_position['cam1'] = 0
            self.__state.pass_direction = "LEFT"
            ''' Max 6 second run '''
            self.__state.pass_abort_time = time.time() + 6.0
            logger.info("Initiating time run from cam 2 <--")
            event.emit(SpeedLogic.EVENT_PASS_START, cam)

        ''' Check for end of LEFT pass on camera 1 '''
        if cam == 'cam1' and self.__state.pass_direction == "LEFT" and motion_tracker_done_message.get_direction() == -1:
            ''' Ending run on Cam 1 '''
            self.__state.pass_position['cam1'] = motion_tracker_done_message.get_position()
            self.__state.pass_direction = None
            logger.info("Timed run completed on cam 2 <--")
            ''' Clear the abort time since the pass is complete '''
            self.__state.pass_abort_time = None

            speed_pass_message = SpeedPassMessage(
                'LEFT',
                self.__state.pass_position['cam2'],
                self.__state.cameras_data.get_frame('cam2', self.__state.pass_position['cam2']).get_timestamp(),
                self.__state.pass_position['cam1'],
                self.__state.cameras_data.get_frame('cam1', self.__state.pass_position['cam1']).get_timestamp(),                
            )
            self.__check_announcement(speed_pass_message)
            event.emit(SpeedLogic.EVENT_PASS_END, speed_pass_message)

    def set_distance(self, distance: int):
        self.__state.distance = distance

    def get_distance(self):
        return self.__state.distance

    def __check_announcement(self, speed_pass_message: SpeedPassMessage):
      milliseconds = speed_pass_message.timestamp_end - speed_pass_message.timestamp_start

      kilometer = float(self.__state.distance) / 1000
      hours = float(milliseconds) / 1000 / 60  / 60

      if (hours > 0):
         kmh = kilometer / hours
      else:
         kmh = 0

      if (kmh >= 500):
         logger.warning("Do not add announcement exceeding 500 km/h")
         return

      if speed_pass_message.direction == 'RIGHT':
         self.__add_announcement(
            speed_pass_message.position_start, 
            speed_pass_message.timestamp_start, 
            speed_pass_message.position_end,
            speed_pass_message.timestamp_end, 
            kmh,
            1)
      else:
         self.__add_announcement(
            speed_pass_message.position_end, 
            speed_pass_message.timestamp_end, 
            speed_pass_message.position_start,
            speed_pass_message.timestamp_start, 
            kmh,
            -1)

    def __add_announcement(self, cam1_frame_number, cam1_timestamp, cam2_frame_number, cam2_timestamp, speed, direction):
        milliseconds = abs(cam1_timestamp - cam2_timestamp)
        announcement = Announcement(
            cam1_frame_number,
            cam2_frame_number,
            milliseconds,
            speed,
            direction
        )
        self.__state.announcements.append(announcement)
        event.emit(self.EVENT_ANNOUNCEMENT_NEW, announcement)

    def get_announcement_max_speeds(self):
        max_right = None  # type: Announcement
        max_left = None   # type: Announcement
        for announcement in self.__state.announcements.get_announcements():
            ''' Check right direction '''
            if announcement.get_direction() == 1: 
                if max_right is None:
                    max_right = announcement
                    continue
                if max_right.get_speed() > announcement.get_speed(): continue
                max_right = announcement
                continue
            ''' Check left direction '''
            if max_left is None:
                max_left = announcement
                continue
            if max_left.get_speed() > announcement.get_speed(): continue
            max_left = announcement

        return {
            'RIGHT': max_right,
            'LEFT': max_left
        }
        
    def get_announcement_by_index(self, index) -> Announcement:
        return self.__state.announcements.get_announcement_by_index(index)

    def remove_announcement_by_index(self, index):
        self.__state.announcements.remove_announcement_by_index(index)


    def get_time(self, frame: Frame) -> int:
        ''' get time on frame position '''
        t = frame.get_timestamp() - self.__state.cameras_data.get_start_timestamp()
        if t < 0: t =0
        return t
