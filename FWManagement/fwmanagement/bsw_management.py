from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys

import caldav
from caldav import DAVClient
import icalendar

from DavCalendar import DavCalendar
from LdapClient import LdapClient

from tests.conf_private import caldav_servers
url = caldav_servers[0]['url']
# url = 'http://cloud.innovationv2.localdomain/remote.php/caldav/principals/Andreas_Gremm/'
username = caldav_servers[0]['username']
password = caldav_servers[0]['password']
davclient = DavCalendar(url=url, username=username, password=password, calendarname='Brandsicherheitswachen')
calendars=davclient.get_calendarList()
bsw_calendar=davclient.get_calendar()

userdn="cn=Andreas Gremm,ou=mettmann,o=fw,dc=users,dc=bos,dc=de"
ldapclient = LdapClient("cloud.innovationv2.localdomain", "dc=bos,dc=de", userdn, password)

print("Here is some icalendar data:")
print(davclient.eventCursor, davclient.eventsNum)
davclient.fetch_events(start=datetime(2020, 1, 1), end=datetime(2021, 1, 1), expand=False)
print(davclient.eventCursor, davclient.eventsNum)
events_fetched = davclient.get_fetchedEvents()
print(events_fetched[0].data)
event = davclient.get_currentEvent()
print(event.data)
eventContent = davclient.get_currentEventContent()
print(eventContent)
bswtemp=davclient.define_BSWEvent(datetime(2020,9,14,12,0), datetime(2020,9,14,13,0), 'Dies ist eine sehr lange Summary mit vielen Zeichen, die hoffentlich gut geht', location='x, y, z', description='a b c ', anzteilnehmer=4, organizer=('Andreas Gremm','andreas.gremm@t-online.de'))

attendee1=davclient.create_attendee('Andreas Gremm','INDIVIDUAL','OPT-PARTICIPANT', 'raspberry.gremm@gmail.com')
attendee2=davclient.create_attendee('Claudia Gremm','INDIVIDUAL','OPT-PARTICIPANT', 'claudia.gremm@gmail.com')

print(attendee1)
davclient.add_uniqueAttendee(attendee1)
davclient.add_uniqueAttendee(attendee1)
davclient.add_uniqueAttendee(attendee2)
attendeeList = davclient.get_attendeeList()
print(attendeeList)




davclient.add_uniqueCategory('ANFRAGE')
davclient.add_uniqueCategory('ANFRAGE')
davclient.add_uniqueCategory('Bedarf=2')
print(eventContent)

davclient.change_category('ANFRAGE', 'ANFRAGE-ABGESCHLOSSEN')
print(eventContent)

davclient.set_status('TENTATIVE')
print(eventContent)
davclient.set_status('CONFIRMED')
print(eventContent)


#davclient.fetch_events(start=datetime(2021, 1, 1), end=datetime(2022, 1, 1), expand=True)
#print(davclient.eventCursor, davclient.eventsNum)
#http://0.0.0.0:8089/bsw/add-event-members/9256cc77-a124-4b92-90a1-2ffb27d3e4a6
