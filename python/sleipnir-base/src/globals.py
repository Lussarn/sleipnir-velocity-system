import logging 

import event
from database.db import DB
from camera_server import CameraServer

'''
Globals.EVENT_FLIGHT_CHANGE flight: int          : the flight have changed
Globals.EVENT_GROUND_LEVEL_CHANGE value: int     : the ground level hanve changed
'''

logger = logging.getLogger(__name__)

class GlobalState:
    def __init__(self):
        ''' database '''
        self.db = None

        ''' flight number (1-20) '''
        self.flight = 1
        ''' ground level, no tracking below this '''
        self.ground_level = 400

        ''' Are the cameras online '''
        self.camera_online = {
            'cam1': False,
            'cam2': False
        }

class Globals:
    EVENT_FLIGHT_CHANGE         = "globals.flight.change"
    EVENT_GROUND_LEVEL_CHANGE   = "globals.ground_level.change"

    def __init__(self, db: DB):
        self.__state = GlobalState()
        self.__state.db = db

        event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_camera_online)
        event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camera_offline)

        ''' Listen to the stop event from speed_logic, to load the newly flown flight '''
        from speed_logic import SpeedLogic
        event.on(SpeedLogic.EVENT_SPEED_STOP, self.__evt_speedlogic_speed_stop)

    def __evt_camera_online(self, cam):
        self.__state.camera_online[cam] = True

    def __evt_camera_offline(self, cam):
        self.__state.camera_online[cam] = False

    def __evt_speedlogic_speed_stop(self):
        ''' Load the flight if a speed stop event occurs '''
        self.set_flight(self.__state.flight)

    '''
    db functions
    '''
    def get_db(self) -> DB:
        return self.__state.db

    '''
    flight functions
    '''
    def set_flight(self, flight):
        self.__state.flight = flight
        event.emit(Globals.EVENT_FLIGHT_CHANGE, flight)

    def get_flight(self):
        return self.__state.flight

    '''
    ground level functions
    '''
    def set_ground_level(self, ground_level):
        self.__state.ground_level = ground_level
        event.emit(Globals.EVENT_GROUND_LEVEL_CHANGE, ground_level)
    
    def get_ground_level(self):
        return self.__state.ground_level
