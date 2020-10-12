from json import JSONEncoder

from cryptography.fernet import Fernet
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# import paho.mqtt.publish as publish

# if _platform == "cygwin":
#    mqtt = {"hostname": "192.168.1.238", "port": 1883, "auth": None}
# else:
#    mqtt = {
#        "hostname": "localhost",
#        "port": 1883,
#        "auth": {"username": "ffmgmt", "password": "LS3y1MoNw81n8dNbtbnE"},
#    }

"""
 Klasse Benutzer

"""


class Benutzer(UserMixin):
    @staticmethod
    def decrypt_password(encrypted_password):
        return (
            Fernet(current_app.config["USER_KEY"])
            .decrypt(encrypted_password.encode())
            .decode()
        )

    def __init__(
        self,
        username,
        passwort,
        id,
        email,
        vorname,
        nachname,
        employeeType,
        dn,
        principal=None,
        calendarhost=None,
        bswcalendar=None
    ):
        self.username = username
        self.passwort = generate_password_hash(passwort, method="sha256")
        self.vorname = vorname
        self.nachname = nachname
        self.email = email
        self.role = "Self_Read"
        self.id = id
        self.dn = dn
        self.employeeType = employeeType
        self.calendarHost = calendarhost
        self.principal = principal or self.vorname + "_" + self.nachname
        self.bswCalendar = bswcalendar
        self.temp = (
            Fernet(current_app.config["USER_KEY"])
            .encrypt(passwort.encode())
            .decode()
        )

    def change_defaults(self, destinationIndicator, calendarHost, bswCalendar):
        self.calendarHost = calendarHost
        self.bswCalendar = bswCalendar

        if len(destinationIndicator) > 0:
            for indicator in destinationIndicator:
                entrylist = indicator.split("?")
                if self.calendarHost == entrylist[0]:
                    for entry in entrylist:
                        if "PRINCIPAL" in entry:
                            self.principal = entry.split("=")[1]
                        if "BSWCALENDAR" in entry:
                            self.bswCalendar = entry.split("=")[1]

    def get_password(self):
        return (
            Fernet(current_app.config["USER_KEY"])
            .decrypt(self.temp.encode())
            .decode()
        )

    def set_profile(self, ldapwriter):
        pass

    def __repr__(self):
        return u"<User %s, (%s, %s)>" % (
            self.username,
            self.vorname,
            self.nachname,
        )

    """
     Funktionen zum Testen des Passworts.
     Eingabe: password = Klartext Passwort
    """

    def check_password(self, password):
        check_password_hash(self.password, password)


class BenutzerEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
