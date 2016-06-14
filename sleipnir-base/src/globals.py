"""
Global Config variables 
"""
import sys

# Program name
PROGRAM_NAME = "Sleipnir velocity system"

# Program version
VERSION = "v0.1.0"


if sys.platform.startswith("linux"):
    OS = "linux"
elif sys.platform.startswith("darwin"):
    OS = "osx"
elif sys.platform.startswith("win32"):
    OS = "windows"
else:
    print "Unknown OS"
    exit
