from logging import setLoggerClass
import requests
import time
import sys
import base64


sys.path.insert(0, '../sleipnir-base/src')

from Configuration import Configuration
from database.DB import DB
import database.frame_dao as frame_dao
from Frame import Frame

cfg = Configuration('../sleipnir-base/sleipnir.yml')
db = DB(cfg.get_or_throw('save_path'))
flight = 2
fps = 90

url = "http://terminator.lan:8000/"

class Camera:
    STATE_IDLE = 0
    STATE_UPLOADING = 1

    def __init__(self, cam):
        self.__state = Camera.STATE_IDLE
        self.__cam = cam
        self.__position = 0

    def set_state(self, state):
        self.__state = state

    def get_state(self):
        return self.__state

    def get_cam(self):
        return self.__cam

    def set_position(self, position):
        self.__position = position

    def get_position(self):
        return self.__position

cams = [
    Camera('cam1'),
    Camera('cam2'),
]

while True:

    start = time.start()

    for cam_idx in range(2):
        cam = cams[cam_idx]

        if cam.get_state() == Camera.STATE_IDLE:
            response = requests.post(url, data = { 'action': 'startcamera', 'id': cam.get_cam() }, timeout=1)
            if (response.status_code != 200):
                raise Exception("Sleipnir base gave error: " + response.status_code + " exiting!")
            if (response.content == b'OK-START'):
                cam.set_state(Camera.STATE_UPLOADING)
                cam.set_position(1)

        if (cam.get_state() == Camera.STATE_UPLOADING):
            position = cam.get_position()
            cam.set_position(position + 1)
            frame = frame_dao.load(db, flight, 1 if cam=='cam1' else 2, position)
            response = requests.post(url, data = { 
                'action': 'uploadframe', 
                'id': cam.get_cam(),
                'framenumber': frame.get_position(),
                'timestamp': frame.get_timestamp(),
                'data': base64.encodebytes(frame.get_image())
                }, timeout=1)
            if (response.status_code != 200):
                raise Exception("Sleipnir base gave error: " + response.status_code + " exiting!")
            if (response.content == b'OK-STOP'):
                cam.set_state(Camera.STATE_IDLE)

#            time.sleep(1)


    # FIXME: implement real rate
    time.sleep(0.001)
