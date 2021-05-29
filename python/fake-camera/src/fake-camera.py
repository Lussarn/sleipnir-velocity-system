import requests
import time

url = "http://localhost:8000/"


class Camera:
    STATE_IDLE = 0
    STATE_UPLOADING = 1

    def __init__(self):
        self.state = Camera.STATE_IDLE

while True:
    response = requests.post(url, data = {'action': 'startcamera', 'id': 'cam1'}, timeout=1)
    time.sleep(1)
