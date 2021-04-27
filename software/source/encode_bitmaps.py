#!/usr/bin/env python

"""
This is a way to save the startup time when running img2py on lots of
files...
"""

import sys
from wx.tools import img2py


command_lines = [
    "   -F -i -n appIcon resources/app_icon.ico images.py",
    "-a -F -c  -n 1 resources/band1.png images.py",
    "-a -F -c -n 2 resources/band2.png images.py",
    "-a -F -c -n 3 resources/band3.png images.py",
    "-a -F -c -n 4 resources/band4.png images.py",
    "-a -F -c -n 5 resources/band5.png images.py",
    "-a -F -c -n 6 resources/band6.png images.py",
    "-a -F -c -n 7 resources/band7.png images.py",
    "-a -F -c -n 8 resources/band8.png images.py",
    "-a -F -n bypass resources/bypass.png images.py",
    "-a -F -n logo resources/logo.png images.py"
    ]


if __name__ == "__main__":
    for line in command_lines:
        args = line.split()
        img2py.main(args)

