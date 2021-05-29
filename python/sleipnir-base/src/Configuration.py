import sys 

import yaml

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
    