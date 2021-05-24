"""
Various Util functions
"""

import PySide2
from PySide2 import QtCore, QtGui
import math
import os
import sys

import globals

def resource_path(relative_path):
    """
    Return base path to analyzer

    PyInstaller creates a temp folder and stores path in _MEIPASS

    use resource path when loading an asset such as an image
    to get the correct path
    """

    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, "assets", relative_path)