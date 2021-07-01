import simplejpeg
from errors import NotFoundError

from database.db import DB

class Frame:
    def __init__ (self, flight: int, cam: str, position: int, timestamp: int, image):
        self.__flight = flight
        self.__cam = cam
        self.__position = position
        self.__timestamp = timestamp
        self.__image = image

    def get_flight(self):
        return self.__flight

    def get_cam(self):
        return self.__cam

    def get_position(self):
        return self.__position

    def get_timestamp(self):
        return self.__timestamp

    def get_image(self):
        return self.__image

    def set_image(self, image):
        self.__image = image

    def pop_image_load_if_missing(self, db :DB, game: str):
        ''' If there is and image set, returns the image and blank the memory
            If there is no image, trye to load and return it '''
        if self.__image is None:
            import database.frame_dao as frame_dao
            frame = frame_dao.load(db, game, self.__flight, self.__cam, self.__position)
            if frame is None:
                raise NotFoundError("Frame not found")
            return simplejpeg.decode_jpeg(frame.get_image(), colorspace='GRAY')
        else:
            image = self.__image
            self.__image = None
            return image
