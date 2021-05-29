import requests
import time

url = "http://localhost:8000/"


class Camera:
    STATE_IDLE = 0
    STATE_UPLOADING = 1

    def __init__(self, cam):
        self.__state = Camera.STATE_IDLE
        self.__cam = cam

    def get_state(self):
        return self.__state

    def get_cam(self):
        return self.__cam

cams = [
    Camera('cam1'),
    Camera('cam2'),
]


while True:
    for cam_idx in range(2):
        cam = cams[cam_idx]

        if cams[cam_idx].get_state() == Camera.STATE_IDLE:
            response = requests.post(url, data = { 'action': 'startcamera', 'id': cam.get_cam() }, timeout=1)

    time.sleep(0.011)
