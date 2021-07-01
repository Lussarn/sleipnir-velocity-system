import logging
from errors import IllegalStateError

import event
from globals import Globals
from frame import Frame
from camera_server import CameraServer
from cameras_data import CamerasData
from game.align.events import *


logger = logging.getLogger(__name__)

class AlignState: 
    def __init__(self):        
        ''' collection of frames '''
        self.cameras_data = None    # type: CamerasData

        ''' Are the Cameras aligning?
        possible values: None, cam1, cam2 '''
        self.cam_aligning = None    # type: str

class Logic:

    def __init__(self, globals :Globals, camera_server :CameraServer):
        self.__globals = globals
        self.__state = AlignState()
        self.__camera_server = camera_server
        event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camerserver_camera_offline)

    def __evt_camerserver_camera_offline(self, cam):
        ''' Stop aligning camera if we are doing it '''
        if self.__state.cam_aligning is not None:
            self.stop_align_camera(self.__state.cam_aligning)

    '''
    Aligning of the camera function start
    '''
    def start_align_camera(self, cam :str):
        if self.__state.cam_aligning == cam:
            ''' Camera is already aligning '''
            raise IllegalStateError("Camera is already aligning")
        self.__globals.set_flight(1)
        event.on(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.cam_aligning = cam

        import database.frame_dao as frame_dao
        logger.info("Deleting Frames for flight %d, hang on..." % self.__globals.get_flight())
        frame_dao.delete_flight(self.__globals.get_db(), Globals.GAME_ALIGN ,self.__globals.get_flight())

        self.__state.cameras_data = CamerasData(self.__globals.get_db(), self.__globals.get_game(), self.__globals.get_flight())
        self.__camera_server.start_shooting(self.__state.cameras_data)
        event.emit(EVENT_ALIGN_START, cam)
    
    def stop_align_camera(self, cam: str) -> bool:
        if self.__state.cam_aligning != cam:
            ''' Camera is not aligning '''
            raise IllegalStateError("Camera is already aligning")
            
        event.off(CameraServer.EVENT_NEW_FRAME, self.__cameraserver_evt_new_frame)
        self.__state.cam_aligning = None
        self.__camera_server.stop_shooting()

        event.emit(EVENT_ALIGN_STOP, cam)

    def __cameraserver_evt_new_frame(self, frame :Frame):
        if frame.get_cam() == self.__state.cam_aligning:
            event.emit(EVENT_ALIGN_FRAME_NEW, frame)
        return

