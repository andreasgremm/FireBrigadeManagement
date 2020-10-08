# -*- coding: utf-8 -*-
import caldav
import vobject
import pytz

local_tz = pytz.timezone("Europe/Berlin")
debug = False

BSWEventStart = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Feuerwehr Mettmann//Innovation//EN
BEGIN:VEVENT
STATUS:TENTATIVE
"""

BSWEventEnd = """BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-PT2H
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-P1D
END:VALARM
BEGIN:VALARM
ACTION:DISPLAY
TRIGGER;RELATED=START:-P2D
END:VALARM
END:VEVENT
END:VCALENDAR
"""


class DavCalendar(object):
    """docstring for BSWCalendar."""

    def __init__(self, url, username, password, calendarname):
        self.__client = caldav.DAVClient(
            url=url, username=username, password=password
        )
        self.__principal = self.__client.principal()
        self.__calendars = self.__principal.calendars()
        # self.url = url
        # self.username = username
        # self.password = password
        self.__calendar_url = None
        self.__calendar_name = None
        self.__calendar = None
        self.__last_event_list = []
        self.eventsNum = 0
        self.eventCursor = None

        if self.__calendars:
            for c in self.__calendars:
                if calendarname in c.name:
                    self.__calendar_url = c.url
                    self.__calendar_name = c.name
                    self.__calendar = c

    def get_calendarList(self):
        return self.__calendars

    def get_calendarUrl(self):
        return self.__calendar_url

    def get_calendarName(self):
        return self.__calendar_name

    def get_calendar(self):
        return self.__calendar

    def fetch_events(self, start, end, expand=False):
        self.__last_event_list = self.__calendar.date_search(
            start=start, end=end, expand=expand
        )
        self.eventsNum = len(self.__last_event_list)
        if self.eventsNum > 0:
            self.eventCursor = 0
        else:
            self.eventCursor = None

    def get_fetchedEvents(self):
        return self.__last_event_list

    def get_currentEvent(self):
        if self.eventCursor is not None:
            return self.__last_event_list[self.eventCursor]
        else:
            return None

    def get_currentEventContent(self):
        if self.eventCursor is not None:
            return self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents
        else:
            return None

    def get_nextEvent(self):
        if self.eventCursor is not None:
            if self.eventCursor < self.eventsNum-1:
                self.eventCursor += 1
                return self.__last_event_list[self.eventCursor]
            else:
                return None
        else:
            return None

    def set_eventCursor(self, id):
        if id in range(0, self.eventsNum):
            self.eventCursor = id
            return id
        return None

    def set_eventCursorfromUID(self, uid):
        for idx, entry in enumerate(self.__last_event_list):
            if entry.vobject_instance.vevent.contents["uid"][0].value == uid:
                self.eventCursor = idx
                return idx
        return None

    def fetch_eventbyUID(self, uid):
        self.__last_event_list = []
        self.eventsNum = 0
        self.eventCursor = None
        try:
            self.__last_event_list = [self.__calendar.event_by_uid(uid)]
            self.eventsNum = len(self.__last_event_list)
            if self.eventsNum > 0:
                self.eventCursor = 0
        except Exception as err:
            if debug:
                print(err)

    def create_attendee(self, cn, cutype, role, mail, partstat='NEEDS-ACTION', rsvp="TRUE"):
        params = {
            "CN": [cn],
            "CUTYPE": [cutype],
            "ROLE": [role],
            "PARTSTAT": [partstat],
            "RSVP": [rsvp],
        }
        attendee = vobject.base.ContentLine(
            name="attendee", params={}, value=mail
        )
        attendee.params = params
        return attendee

    def get_attendeeList(self):
        if (
            "attendee"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            return self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.attendee_list
        return []

    def find_attendee(self, mail):
        for attendee in self.get_attendeeList():
            if mail == attendee.value.split(':')[1]:
                return attendee
        return None

    def add_uniqueAttendee(self, attendee):
        if (
            "attendee"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            if (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["attendee"]
                .count(attendee)
                == 0
            ):
                self.__last_event_list[
                    self.eventCursor
                ].vobject_instance.vevent.contents["attendee"].append(
                    attendee
                )
        else:
            self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["attendee"] = [attendee]

    def delete_attendee(self, attendee):
        if (
            "attendee"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            if (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["attendee"]
                .count(attendee)
                != 0
            ):
                self.__last_event_list[
                    self.eventCursor
                ].vobject_instance.vevent.contents["attendee"].remove(
                    attendee
                )

    def add_uniqueCategory(self, category):
        if (
            "categories"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            categories = self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["categories"][0]

            if categories.value.count(category) == 0:
                categories.value.insert(0, category)
        else:
            categories = vobject.base.ContentLine(
                name="categories", params={}, value=[category]
            )
            self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["categories"] = [categories]

    def change_category(self, old_category, new_category):
        if (
            "categories"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            categories = self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["categories"][0]

            if categories.value.count(old_category) > 0:
                categories.value.remove(old_category)
                categories.value.insert(0, new_category)
        else:
            self.add_uniqueCategory(new_category)

    def get_categoryList(self):
        if (
            "categories"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            return self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.categories_list
        return []

    def test_category(self, category):
        category_list = self.get_categoryList()
        for c in category_list:
            if category in c.value:
                return True
        return False

    def delete_category(self, category):
        deleted = False
        category_list = self.get_categoryList()
        for c in category_list:
            if category in c.value:
                c.value.remove(category)
                deleted = True
        return deleted

    def set_status(self, status):
        if (
            "status"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["status"][0].value = status
        else:
            status = vobject.base.ContentLine(
                name="status", params={}, value=status
            )
            self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents["status"] = [status]

    def get_eventStart(self, string=True, strformat="%a %d-%m-%Y %H:%M (%Z)"):
        if string:
            return (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["dtstart"][0]
                .value.replace(tzinfo=pytz.utc)
                .astimezone(local_tz)
                .strftime(strformat)
            )
        else:
            return (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["dtstart"][0]
                .value.replace(tzinfo=pytz.utc)
                .astimezone(local_tz)
            )

    def get_eventEnd(self, string=True, strformat="%a %d-%m-%Y %H:%M (%Z)"):
        if string:
            return (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["dtend"][0]
                .value.replace(tzinfo=pytz.utc)
                .astimezone(local_tz)
                .strftime(strformat)
            )
        else:
            return (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["dtend"][0]
                .value.replace(tzinfo=pytz.utc)
                .astimezone(local_tz)
            )

    def get_eventDuration(self):
        return (
            self.__last_event_list[self.eventCursor]
            .vobject_instance.vevent.contents["dtend"][0]
            .value
            - self.__last_event_list[self.eventCursor]
            .vobject_instance.vevent.contents["dtstart"][0]
            .value
        )

    def get_eventSummary(self):
        if (
            "summary"
            in self.__last_event_list[
                self.eventCursor
            ].vobject_instance.vevent.contents.keys()
        ):
            return (
                self.__last_event_list[self.eventCursor]
                .vobject_instance.vevent.contents["summary"][0]
                .value
            )
        return ""

    def define_BSWEvent(
        self,
        start,
        end,
        summary,
        location,
        description,
        anzteilnehmer=None,
        organizer=None,
    ):
        dtstart = (
            "DTSTART;TZID=Europe/Berlin:"
            + start.strftime("%Y%m%dT%H%M%S")
            + "\n"
        )
        dtend = (
            "DTEND;TZID=Europe/Berlin:" + end.strftime("%Y%m%dT%H%M%S") + "\n"
        )
        categories = "CATEGORIES:BSW-ANFRAGE"
        if anzteilnehmer is not None:
            categories += ",Bedarf=" + str(anzteilnehmer)
        categories += "\n"
        bswtemp = vobject.readOne(
            BSWEventStart + dtstart + dtend + categories + BSWEventEnd
        )
        bswtemp.vevent.add("summary").value = summary
        bswtemp.vevent.add("description").value = description
        bswtemp.vevent.add("location").value = location
        if organizer is not None:
            tname, tmail = organizer
            tparams = {"CN": [tname]}
            bswtemp.vevent.add("organizer").value = "mailto:" + tmail
            bswtemp.vevent.contents["organizer"][0].params = tparams
        return bswtemp.serialize()

    def save_event(self, event):
        return self.__calendar.save_event(event)
