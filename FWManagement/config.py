import os
from cryptography.fernet import Fernet

basedir = os.path.abspath(os.path.dirname(__file__))
CSRF_ENABLED = True
SECRET_KEY = os.urandom(24)
USER_KEY = Fernet.generate_key()

BSW_CALENDAR = "Brandsicherheitswache"
CALENDAR_HOST_TYP = "NEXTCLOUD"
CALENDAR_HOST = "http://cloud.innovationv2.localdomain/"
CALENDAR_MONTH_DEFAULT = 4
BSW_FOOTER_DIENSTANWEISUNG = "<Link zur Dienstanweisung>"
BSW_FOOTER_MELDEFORMULAR = "<Link zum Meldeformular>"
BSW_FOOTER_TELEFON = "tel:<Nummer des DGL>"
BSW_FOOTER_EMAIL = "mailto:<Email-Adresse des BSW-MGMT>"
BSW_TEILNEHMER_BEDARF = 2
