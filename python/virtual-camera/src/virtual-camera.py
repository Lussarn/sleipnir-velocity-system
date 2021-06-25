from logging import setLoggerClass
import requests
import time
import sys

sys.path.insert(0, '../sleipnir-base/src')

from configuration import Configuration
from database.db import DB
import database.frame_dao as frame_dao
from frame import Frame

def usage():
    print ('Usage:')
    print ('fake-camera N')
    print ('N - flight')
    exit(1)

cfg = Configuration('../sleipnir-base/sleipnir.yml')
db = DB(cfg.get_or_throw('save_path'))
fps = 90

try:
    flight = int(sys.argv[1])
except Exception as e:
    usage()

if flight < 2 or flight > 20:
    usage()

jump = 0
if len(sys.argv) > 2:
    jump = int(sys.argv[2])

url = "http://127.0.0.1:8000/"

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

session = requests.session()
start = time.time()
count  = 0
while True:
    ''' Rate limit  to fps '''
    if count > (time.time() - start) * fps:
        time.sleep(0.001)
        continue
    count += 1    

    for cam_idx in range(2):
        cam = cams[cam_idx]

        if cam.get_state() == Camera.STATE_IDLE:
            response = session.post(url + "?action=startcamera&cam=" + cam.get_cam(), timeout=1)
            if (response.status_code != 200):
                raise Exception("Sleipnir base gave error: " + response.status_code + " exiting!")
            if (response.content == b'OK-START'):
                start = time.time()
                count  = 0
                cam.set_state(Camera.STATE_UPLOADING)
                cam.set_position(1)

        if (cam.get_state() == Camera.STATE_UPLOADING):
            position = cam.get_position()
            cam.set_position(position + 1)
            frame = frame_dao.load(db, "speed_trap", flight, cam.get_cam(), position + jump)
            response = session.post(url + "?action=uploadframe&cam=" + cam.get_cam() + "&position=" + str(frame.get_position() - jump ) + "&timestamp=" + str(frame.get_timestamp()), 
                data=frame.get_image(),
                timeout=1)
            if (response.status_code != 200):
                raise Exception("Sleipnir base gave error: " + response.status_code + " exiting!")
            if (response.content == b'OK-STOP'):
                cam.set_state(Camera.STATE_IDLE)
