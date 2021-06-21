from PySide2 import QtCore

import logging
import Event

from database.DB import DB
from Frame import Frame
from CameraServer import CameraServer
from CamerasData import CamerasData

logger = logging.getLogger(__name__)

'''
ActionLogic emits the following events

ActionLogic.EVENT_ALIGN_START cam :str               : Start aligning camera
ActionLogic.EVENT_ALIGN_STOP  cam :str               : Stop aligning camera
ActionLogic.EVENT_ALIGN_NEW_FRAME frame :Frame       : An aligning camera have a new frame
'''

class ActionState:
    def __init__(self):
        self.flight = 1
        self.cameras_data = None

        self.camera_online = {
            'cam1': False,
            'cam2': False
        }

        self.camera_aligning = None

        self.videos = {
            'cam1': None,
            'cam2': None
        }

class ActionLogic:
    EVENT_ALIGN_START     = "actionlogic.align_start"
    EVENT_ALIGN_STOP      = "actionlogic.align_stop"
    EVENT_ALIGN_NEW_FRAME = "actionlogic.align_new_frame"

    def __init__(self, qobject, db :DB, camera_server :CameraServer, videos):
        self.__timer = None
        self.__qobject = qobject
        self.__action_state = ActionState()
        self.__action_state.videos['cam1'] = videos[0]
        self.__action_state.videos['cam2'] = videos[1]
        self.__db = db
        self.__camera_server = camera_server
        Event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_camera_online)
        Event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camera_offline)
        
    def get_action_state(self):
        return self.__action_state

    def __evt_camera_online(self, cam):
        self.__action_state.camera_online[cam] = True

    def __evt_camera_offline(self, cam):
        self.__action_state.camera_online[cam] = False

        ''' Stop aligning camera if we are doing it '''
        if self.__action_state.camera_aligning != None:
            self.stop_align_camera(self.__action_state.camera_aligning)

    def start_align_camera(self, cam :str):
        if self.__action_state.camera_aligning == cam:
            ''' Camera is already aligning '''
            return
        Event.on(CameraServer.EVENT_NEW_FRAME, self.__align_evt_new_frame)
        self.__action_state.camera_aligning = cam

        self.__action_state.videos[cam].set_shooting(True) # Diable GUI, fo not belong here
        self.__action_state.cameras_data = CamerasData(self.__db, self.__action_state.flight)
        self.__action_state.videos[cam].cameras_data = self.__action_state.cameras_data
        self.__camera_server.start_shooting(
            self.__action_state.flight,
            self.__action_state.cameras_data
        )
        Event.emit(ActionLogic.EVENT_ALIGN_START, cam)
    
    def stop_align_camera(self, cam: str) -> bool:
        if self.__action_state.camera_aligning != cam:
            ''' Camera is not aligning '''
            return
        self.__action_state.camera_aligning = None
        self.__camera_server.stop_shooting()

        Event.emit(ActionLogic.EVENT_ALIGN_STOP, cam)

    def __align_evt_new_frame(self, frame :Frame):
        if "cam" + str(frame.get_camera()) == self.__action_state.camera_aligning:
            Event.emit(ActionLogic.EVENT_ALIGN_NEW_FRAME, frame)
        return
