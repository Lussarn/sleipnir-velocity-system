import Event
from database.DB import DB
from CameraServer import CameraServer

'''
Globals.EVENT_FLIGHT_CHANGE flight: int          : the flight have changed
Globals.EVENT_GROUND_LEVEL_CHANGE value: int     : the ground level hanve changed
'''

class GlobalState:
    def __init__(self, db: DB):
        ''' database '''
        self.db = db

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
        self.__state = GlobalState(db)
        self.__state.db = db
        Event.on(CameraServer.EVENT_CAMERA_ONLINE, self.__evt_camera_online)
        Event.on(CameraServer.EVENT_CAMERA_OFFLINE, self.__evt_camera_offline)

    def __evt_camera_online(self, cam):
        self.__state.camera_online[cam] = True

    def __evt_camera_offline(self, cam):
        self.__state.camera_online[cam] = False

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
        Event.emit(Globals.EVENT_FLIGHT_CHANGE, flight)

    def get_flight(self):
        return self.__state.flight

    '''
    ground level functions
    '''
    def set_ground_level(self, ground_level):
        self.__state.ground_level = ground_level
        Event.emit(Globals.EVENT_GROUND_LEVEL_CHANGE, ground_level)
    
    def get_ground_level(self):
        return self.__state.ground_level
