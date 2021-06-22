import logging

import Event
from Globals import Globals
from Frame import Frame
from CameraServer import CameraServer
from CamerasData import CamerasData

logger = logging.getLogger(__name__)

'''
AlignLogic emits the following events

AlignLogic.EVENT_ALIGN_START cam :str               : Start aligning camera
AlignLogic.EVENT_ALIGN_STOP  cam :str               : Stop aligning camera
AlignLogic.EVENT_ALIGN_NEW_FRAME frame :Frame       : An aligning camera have a new frame
'''

class AlignState: 
    def __init__(self):        
        ''' collection of frames '''
        self.cameras_data = None

        ''' Are the Cameras aligning '''
        self.camera_aligning = None

class AlignLogic:
    EVENT_ALIGN_START           = "alignlogic.align.start"
    EVENT_ALIGN_STOP            = "alignlogic.align.stop"
    EVENT_ALIGN_NEW_FRAME       = "alignlogic.align.new_frame"

    def __init__(self, globals :Globals, camera_server :CameraServer):
        self.__globals = globals
        self.__state = AlignState()
        self.__camera_server = camera_server
        Event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camera_offline)
        
    def __evt_camera_offline(self, cam):
        ''' Stop aligning camera if we are doing it '''
        if self.__state.camera_aligning != None:
            self.stop_align_camera(self.__state.camera_aligning)

    '''
    Aligning of the camera function start
    '''
    def start_align_camera(self, cam :str):
        if self.__state.camera_aligning == cam:
            ''' Camera is already aligning '''
            return
        self.__globals.set_flight(1)
        Event.on(CameraServer.EVENT_NEW_FRAME, self.__align_evt_new_frame)
        self.__state.camera_aligning = cam

        self.__state.cameras_data = CamerasData(self.__globals.get_db(), self.__globals.get_flight())
        self.__camera_server.start_shooting(
            self.__globals.get_flight(),
            self.__state.cameras_data
        )
        Event.emit(AlignLogic.EVENT_ALIGN_START, cam)
    
    def stop_align_camera(self, cam: str) -> bool:
        if self.__state.camera_aligning != cam:
            ''' Camera is not aligning '''
            return
        self.__state.camera_aligning = None
        self.__camera_server.stop_shooting()

        Event.emit(AlignLogic.EVENT_ALIGN_STOP, cam)

    def __align_evt_new_frame(self, frame :Frame):
        if frame.get_cam() == self.__state.camera_aligning:
            Event.emit(AlignLogic.EVENT_ALIGN_NEW_FRAME, frame)
        return

