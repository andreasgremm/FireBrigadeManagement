# Feuerwehr Management
Das Programm Feuerwehr-Management dient zur Unterstützung der Verwaltung einer Feuerwehr.

Als Basis dient ein LDAP-Verzeichnis für die Verwaltung der Benutzer, Benutzergruppen und deren Berechtigungen, sowie eine NextCloud Installation für die eigentliche Organisationsarbeit.

**Feuerwehr Management** wird verschiedene Funktionalitäten erhalten und ist in dieser Form die Ablöse einer früheren Eigenentwicklung deren Funktionen durch andere kommerzielle Programme teilweise abgelöst wird. Andererseits sind in diesen kommerziellen Programmen einige Funktionalitäten nicht enthalten.

* Cloud Funktionalitäten wie Dateiverwaltung, Kontakte, Kalender, Umfragen, Aufgaben u.a.
* Verwaltung von Brandsicherheitswachen
* Verwaltung von Lehrgängen
* ...

Im ersten Schritt wird die ursprüngliche Verwaltung von Brandsicherheitswachen, welche bei der Feuerwehr Mettmann seit mehreren Jahren auf einem Google-Kalender basierte, auf Basis eines NextCloud Kalenders realisiert.

Die Basis der Programmierung ist *Python 3.x* mit dem Frameworks *Flask* und *BootStrap* mit deren vielfältigen Möglichkeiten.

## Brandsicherheitswachen (BSW)
Die Organisation einer Brandsicherheitswache unterteilt sich in verschiedene Phasen.
Beispielhaft sind folgende Phasen realisiert.

1. Eintragung des Termins in einen Kalender mit zusätzlichen Attributen.
2. Einladung der für Brandsicherheitswachen geschulten Feuerwehrmitglieder zu diesem Termin.
3. Abwarten der Reaktion der eingeladenen Teilnehmer (Zusage, Absage, Eventuell)
4. Bei Erreichen der notwendigen Teilnehmeranzahl kann die Brandsicherheitswache "finalisiert" werden.
5. Bei der Finalisierung werden die Teilnehmer und eine Reserve spezifiziert.
6. Eventuelle Änderungen (nachträgliche Absagen/Zusagen) müssen verwaltet werden.
7. Die durchgeführte Brandsicherheitswache muss abgeschlossen werden (Aufwandsentschädigung anweisen)

Die Nutzung der Anwendung ist im [BSW-Benutzerhandbuch](BSW-Benutzerhandbuch.md) beschrieben.

### Installation
Die Installation kann durch das Klonen dieses GitHub Repositories erfolgen.

![](screenshots/Bildschirmfoto%202020-10-08%20um%2012.45.36.png)

#### Technische Voraussetzungen
* LDAP Verzeichnis
* NextCloud Installation
	* NextCloud Benutzername ist in der Form: *Vorname*_*Nachname* (Konfiguration des Benutzernamens in Zukunft möglich, aktuell nur über Änderung im Programm möglich)
* Python3


Für produktive Anwendung:

* WSGI Funktionalität in einem Webserver 

### Konfiguration

Die Konfiguration ist relativ simple:

* Konfiguration des LDAP-Verzeichnis
	* BSW-Admin Benutzer kennzeichnen
	* BSW-Teilnehmer kennzeichnen
* Konfiguration der Awendung
 	* LDAP-Zugang für die Anwendung konfigurieren
 	* NextCloud Zugang für die Anwendung konfigurieren

Die aktuell realisierte Konfiguration besteht aus einem vorgedachten LDAP-Verzeichnisbaum:

![](screenshots/Bildschirmfoto%202020-10-06%20um%2021.32.00.png)

* Die Benutzer (users) sind mit der Objekt-Klasse *inetOrgPerson* spezifiziert.
* Die Gruppen (groups) sind mit der Objekt-Klasse *groupOfUniqueNames* spezifiziert.
* Die Listen (lists) sind mit der Objekt-Klasse *groupOfURLs* spezifiziert und können als dynamische Gruppen (Overlays) angesehen werden, welche sich auf Basis von Filtern beim Zugriff generieren. Beispiel für eine **memberURL** ```ldap:///o=fw,dc=users,dc=bos,dc=de??sub?(objectClass=inetOrgPerson)(ou=mettmann)(employeeType=bsw)```
 
#### Konfiguration des LDAP-Verzeichnis

* Die Verwalter der BSW bekommen im LDAP-Eintrag den **employeeType** *bswadmin* zugewiesen. (Zwingende Voraussetzung)
* Die Teilnehmer einer BSW bekommen im LDAP-Eintrag den **employeeType** *bsw* zugewiesen. Dieses ermöglicht die einfache Selektierung als Teilnehmer über *Listen*. Es ist ebenfalls eine Selektierung über *Gruppen* möglich, dafür muss der **employeeType** nicht gesetzt werden. Allerdings muss dann der gewünschte Teilnehmer in eine Gruppe aufgenommen werden.
* Alle verwendeten Benutzer (BSW Admin, BSW Teilnehmer) haben mindestens folgende LDAP Attribute gesetzt
	* sn (Nachname)
	* givenName (Vorname)
	* mail (Email Adresse)
	* employeeType (siehe oben, nur beim BSW Admin zwingend)

#### Konfiguration der Anwendung
Für die Konfiguration der LDAP-Zugangsdaten muss ein Python Modul **Security.LDAP** erzeugt werden. 

```
# genutzte Security.LDAP imports ...
# LDAP_USER ist ein Benutzer, der das Verzeichnis browsen darf, um auf Basis bestimmter  Attribute ein DN zu finden (z.B.: zum Einloggen des Benutzers mit einer UID.)
from Security.LDAP import (
    LDAP_BASEDN,
    LDAP_PASSWORD,
    LDAP_SERVER,
    LDAP_USER,
)

# Security.LDAP Beispiel:
# <browseuserpassword> muss mit dem LDAP-Passwort für den "Browseuser" ersetzt werden
LDAP_SERVER = "innovationv2.localdomain"
LDAP_USER = "cn=browseuser,dc=bos,dc=de"
LDAP_PASSWORD = "<browseuserpassword>"
# aktuell nicht genutzt: LDAP_MGMT_GROUP = "(cn=FW-MTM-LG1)"
LDAP_BASEDN = "dc=bos,dc=de"
```

Die Anwendung ist über die Verzeichnisstruktur definiert, alleine das Security.LDAP Modul wird über externe Mechanismen eingebunden. 

Beispiel: \$PYTHONPATH/Security/LDAP.py

```
export PYTHONPATH=~/Documents/git-github/non-git-local-includes
. pythonenv/bin/activate
python fwmanagement.py
```
Das Python-Environment muss mit dem Befehl ```python3 -m venv pythonenv``` erzeugt werden. Innerhalb des Python-Environments müssen die in der Datei *requirements.txt* hinterlegten Module installiert werden. 

```
. pythonenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
In der Datei **config.py** im Hauptverzeichnis müssen folgende Informationen hinterlegt werden:

* Name des NextCloud-Kalenders **BSW_CALENDAR** der genutzt werden soll. (Muss in NextCloud für den Benutzer schreibend zugreifbar sein)
* Host **NEXTCLOUD** des NextCloud-Servers 

Beispiel:

```
BSW_CALENDAR = "Brandsicherheitswache"
NEXTCLOUD = "http://cloud.innovationv2.localdomain/"
```

### Start und Test der Anwendung
Für einen einfachen Test kann die Anwendung auf dem Rechner gestartet werden:

```
(pythonenv) <FWManagement$> python fwmanagement.py
 * Serving Flask app "fwmanagement" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:8089/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 159-430-068
```

Über die URL: *http://0.0.0.0:8089/* lässt sich nun die Anwendung erreichen.

Für eine produktive Nutzung wird man die Anwendung als **WSGI** Anwendung in einem Webserver wie Apache oder NGINX laufen lassen. Desweiteren sollte zwingend in einer produktiven Umgebung der Debug-Modus ausgeschaltet werden. [Hinweise hierzu](https://stackoverflow.com/questions/17309889/how-to-debug-a-flask-app)

