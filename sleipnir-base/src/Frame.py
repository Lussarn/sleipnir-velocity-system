class Frame:
    def __init__ (self, flight: int, camera: int, position: int, timestamp: int, image):
        self.__flight = flight
        self.__camera = camera
        self.__position = position
        self.__timestamp = timestamp
        self.__image = image

    def get_flight(self):
        return self.__flight

    def get_camera(self):
        return self.__camera

    def get_position(self):
        return self.__position

    def get_timestamp(self):
        return self.__timestamp

    def get_image(self):
        return self.__image