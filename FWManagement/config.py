import os
from cryptography.fernet import Fernet

basedir = os.path.abspath(os.path.dirname(__file__))
CSRF_ENABLED = True
SECRET_KEY = os.urandom(24)
USER_KEY = Fernet.generate_key()

BSW_CALENDAR = "Brandsicherheitswache"
CALENDAR_HOST_TYP = "NEXTCLOUD"
CALENDAR_HOST = "http://cloud.innovationv2.localdomain/"
# CALENDAR_HOST = "https://innovation.mettmann.de/nextcloud/"
CALENDAR_MONTH_DEFAULT = 4
