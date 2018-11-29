"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['docker.py']
DATA_FILES = []
NAME = "Docker Tray Tool"
OPTIONS = {
    'plist': {
        'LSUIElement': True,
        'CFBundleName': NAME,
        'CFBundleDisplayName': NAME,
        'NSUserNotificationAlertStyle': 'alert'
        # 'ISBackgroundOnly': True
    },
    'iconfile': 'mydock.icns'
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
