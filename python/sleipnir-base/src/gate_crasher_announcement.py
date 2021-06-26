class GateCrasherAnnouncement:
    def __init__(self, level_name, gate_number, cam, position, timestamp, direction, angle, altitude, time_ms):
        self.__level_name = level_name
        self.__gate_number = gate_number
        self.__cam = cam
        self.__position = position
        self.__timestamp = timestamp
        self.__direction = direction
        self.__angle = angle            # hit is above max dive (NOT IMPLEMENTED)
        self.__altitude = altitude      # LOW, HIGH (NOT IMPLEMENTED)
        self.time_ms = time_ms

    def get_level_name(self) -> str:
        return self.__level_name

    def get_gate_number(self) -> int:
        return self.__gate_number

    def get_cam(self) -> str:
        return self.__cam

    def get_position(self) -> int:
        return self.__position

    def get_timestamp(self) -> int:
        return self.__timestamp

    def get_direction(self) -> str:
        return self.__direction

    def get_angle(self) -> str:
        return self.__angle
    
    def get_altitude(self) -> str:
        return self.__altitude

    def get_time_ms(self) -> int:
        return self.time_ms