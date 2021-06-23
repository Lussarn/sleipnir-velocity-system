import yaml
import os

class ConfigurationError(Exception):
    pass

class Configuration:
    def __init__(self, filename: str):
        self.data = yaml.load(open(filename, "r"), Loader=yaml.FullLoader)

    def __node_from_name(self, name):
        ptr = self.data
        parts = name.split(".")
        for part in parts:
            ptr = ptr[part]
        return ptr

    def get(self, name, default=None):
        try:
            return self.__node_from_name(name)
        except KeyError:
            return (default)

    def get_or_throw(self, name):
        try:
            return self.__node_from_name(name)
        except KeyError:
            raise KeyError(name)
    
    def check_configuration(self):
        self.get_save_path()
        self.get_max_dive_angle()
        self.get_blur_strength()


    def get_save_path(self):
        path = self.get_or_throw("save_path")
        ''' Save path be an existing path '''
        if not os.path.exists(path):
            raise ConfigurationError("save_path: path does not exists")
        return path

    def get_max_dive_angle(self):
        ''' Must be able to convert to float '''
        try:
            max_dive_angle = float(self.get('max_dive_angle', 10.0))
        except ValueError:
            raise ConfigurationError("max_dive_angle: illegal number, " + self.get_or_throw('max_dive_angle'))
        ''' Positive number between 1 and 90 '''
        if max_dive_angle < 1 or max_dive_angle > 90:
            raise ConfigurationError("max_dive_angle: angle must be between 1 and 90 degrees")
        return max_dive_angle

    def get_blur_strength(self):
        ''' Must be able to convert to int '''
        try:
            blur_strength = float(self.get('blur_strength', 4))
        except ValueError:
            raise ConfigurationError("blur_strength: illegal number, " + self.get_or_throw('blur_strength'))
        ''' Positive number between 1 and 5 '''
        if blur_strength < 1 or blur_strength > 5:
            raise ConfigurationError("blur_strength: blur strength must be between 1 and 5")
        return blur_strength
