# -*- coding: utf-8 -*-
import locale
import mimetypes
from ast import literal_eval
from datetime import datetime, timedelta
from io import BytesIO

import pytz
import xlwt
from dateutil.relativedelta import relativedelta

# from fwmanagement.modelle import Email
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from ldap3 import (
    ALL,
    LEVEL,
    SUBTREE,
    AttrDef,
    Attribute,
    Connection,
    Entry,
    ObjectDef,
    OperationalAttribute,
    Reader,
    Server,
    Writer,
)
from werkzeug.datastructures import Headers

from fwmanagement.DavCalendar import DavCalendar
from fwmanagement.formulare import BSWAddForm, BSWSearchForm
from fwmanagement.LdapClient import LdapClient
from Security.LDAP import LDAP_BASEDN, LDAP_SERVER

(
    anfrage,
    anfrageabgeschlossen,
    finalisieren,
    durchgefuehrt,
    abgerechnet,
) = terminFlow = (
    u"BSW-ANFRAGE",
    u"BSW-ANFRAGE-ABGESCHLOSSEN",
    u"BSW-FINALISIEREN",
    u"BSW-DURCHGEFÜHRT",
    u"BSW-ABGERECHNET",
)
terminStatus = {
    u"BSW-ANFRAGE": "#edf00f",  # colorId 5: gelb
    u"BSW-FINALISIEREN": "#f0280f",  # colorId 11: rot
    u"BSW-ANFRAGE-ABGESCHLOSSEN": u"#0ff022",  # colorId 10: grün
    u"BSW-ABGERECHNET": u"#E1E1E1",  # colorId 8: grau
    u"BSW-DURCHGEFÜHRT": u"#5484ED",  # colorId 9: blau
}
local_tz = pytz.timezone("Europe/Berlin")
bswcalendar = "BSW_CALENDAR"
nextcloud = "NEXTCLOUD"

bsw_pages = Blueprint("bsw_pages", __name__, template_folder="templates")


def writexlsheader(sheet, ind):
    col = 0
    for head in [
        u"BSW",
        u"Startzeit",
        u"Name",
        u"Vorname",
        u"Strasse",
        u"Plz",
        u"Ort",
        u"Telefon",
        u"Mobiltelefon",
        u"Email",
        u"Bank",
        u"IBAN",
        u"Veranstaltungsdauer",
        u"Dauer inklusive Rüstzeit",
    ]:
        style = xlwt.easyxf("font: bold 1")
        sheet.write(ind, col, head, style)
        col += 1


@bsw_pages.route("/management", methods=["GET"])
@login_required
def management():
    return render_template(
        "/bsw/management.html",
        dienst=None,
        user=current_user,
        management_form=BSWSearchForm(),
    )


@bsw_pages.route("/show1", methods=["POST"])
@login_required
def show1():
    form = BSWSearchForm()
    if request.method == "POST" and form.validate():
        return redirect(
            url_for(
                "bsw_pages.bswreview",
                months=str(form.monate.data),
                jetztdatumin=form.ddatum.data.strftime("%Y-%m-%d"),
            )
        )
    return redirect(url_for("bsw_pages.management"))


@bsw_pages.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = BSWAddForm()
    # form.bedarf.data = current_app.config["DEFAULT_BSW_TEILNEHMER_BEDARF"]
    if request.method == "POST" and form.validate():
        locale.setlocale(locale.LC_ALL, "de_DE")
        davclient = DavCalendar(
            url=current_app.config[nextcloud]
            + "remote.php/dav/"
            + "principals/users/"
            + current_user.vorname
            + "_"
            + current_user.nachname
            + "/",
            username=current_user.username,
            password=current_user.get_password(),
            calendarname=current_app.config[bswcalendar],
        )

        bsw_calendar = davclient.get_calendar()
        if bsw_calendar is None:
            flash(
                current_app.config[bswcalendar] + u" nicht zugreifbar",
                "danger",
            )
            return redirect(url_for("bsw_pages.management"))

        bswtemp = davclient.define_BSWEvent(
            form.sdatum.data,
            form.edatum.data,
            form.summary.data,
            location=form.location.data,
            description=form.beschreibung.data,
            anzteilnehmer=form.bedarf.data,
            organizer=(
                current_user.vorname + " " + current_user.nachname,
                current_user.email,
            ),
        )

        bsw_event = davclient.save_event(bswtemp)

        return redirect(url_for("bsw_pages.management"))
    return render_template(
        "/bsw/add.html",
        user=current_user,
        form=form,
        do=url_for("bsw_pages.add"),
        management_form=BSWSearchForm(),
    )


@bsw_pages.route("/sendemail2event/<eventid>")
@login_required
def sendemail2event(eventid):
    davclient = DavCalendar(
        url=current_app.config[nextcloud]
        + "remote.php/dav/"
        + "principals/users/"
        + current_user.vorname
        + "_"
        + current_user.nachname
        + "/",
        username=current_user.username,
        password=current_user.get_password(),
        calendarname=current_app.config[bswcalendar],
    )

    bsw_calendar = davclient.get_calendar()
    if bsw_calendar is None:
        flash(current_app.config[bswcalendar] + u" nicht zugreifbar", "danger")
        return redirect(url_for("index"))

    davclient.fetch_eventbyUID(eventid)
    attendees = davclient.get_attendeeList()

    urlnew = u"mailto:"
    for attendee in attendees:
        if attendee.params["PARTSTAT"][0] == "ACCEPTED" and (
            attendee.params["ROLE"][0] == "REQ-PARTICIPANT"
            or attendee.params["ROLE"][0] == "CHAIR"
        ):
            urlnew = urlnew + attendee.value.split(":")[1] + u","
    urlnew = (
        urlnew
        + u"?Subject="
        + davclient.get_eventStart()
        + u" "
        + davclient.get_eventSummary()
    )

    if davclient.test_category(anfrageabgeschlossen):
        urlnew = (
            urlnew
            + u"&body=Liebe Kamerad*innen,%0A"
            + u" vielen Dank für Eure Meldung!%0A%0AIhr seid für die"
            + u" Brandsicherheitswache eingeplant.%0AViele Grüße%0A"
        )

    if davclient.test_category(durchgefuehrt):
        urlnew = (
            urlnew
            + u"&body=Liebe Kamerad*innen,%0A"
            + u" vielen Dank für Eure Teilnahme an der"
            + u" Brandsicherheitswache!%0A%0AGab es besondere Ereignisse"
            + u" oder möchtet Ihr"
            + u" andere Informationen weitergeben?%0A%0AViele Grüße%0A"
        )
    urlnew = urlnew + current_user.vorname + " " + current_user.nachname

    return redirect(urlnew)


@bsw_pages.route("/email2person/<email>")
@login_required
def email2person(email):
    print(email)
    ldapclient = LdapClient(
        LDAP_SERVER, LDAP_BASEDN, current_user.dn, current_user.get_password()
    )
    person = ldapclient.find_byEmail(email, "dc=users," + LDAP_BASEDN)
    print(person)
    return redirect(url_for("bsw_pages.management"))


#    persons = []
#    emailfound = Email.query.filter_by(eadress=email).all()
#    for entry in emailfound:
#        for person in entry.persons:
#            persons.append(person)
#   return render_template(
#        "/personen/index.html",
#        persons=persons,
#        user=current_user,
#        management_form=PersonSearchForm(),
#    )


@bsw_pages.route("/BSW_review/", methods=["GET", "POST"])
@bsw_pages.route("/BSW_review/<months>", methods=["GET", "POST"])
@bsw_pages.route(
    "/BSW_review/<months>/<jetztdatumin>", methods=["GET", "POST"]
)
@login_required
def bswreview(months="-12", jetztdatumin=None):
    locale.setlocale(locale.LC_ALL, "de_DE")
    davclient = DavCalendar(
        url=current_app.config[nextcloud]
        + "remote.php/dav/"
        + "principals/users/"
        + current_user.vorname
        + "_"
        + current_user.nachname
        + "/",
        username=current_user.username,
        password=current_user.get_password(),
        calendarname=current_app.config[bswcalendar],
    )

    bsw_calendar = davclient.get_calendar()
    if bsw_calendar is None:
        flash(current_app.config[bswcalendar] + u" nicht zugreifbar", "danger")
        return redirect(url_for("index"))

    imonths = int(months)
    if jetztdatumin:
        jetztdatum = datetime.strptime(jetztdatumin, "%Y-%m-%d")
    else:
        jetztdatum = datetime.now()

    if imonths < 0:
        start = jetztdatum + relativedelta(months=imonths)
        end = jetztdatum + relativedelta(days=-1)
        bswAttendeeCount = {}
    elif imonths > 0:
        start = jetztdatum
        end = jetztdatum + relativedelta(months=imonths)
        bswAttendeeCount = None
    elif imonths == 0:
        start = jetztdatum
        end = jetztdatum + relativedelta(days=1)
        bswAttendeeCount = None

    davclient.fetch_events(start=start, end=end, expand=False)
    events = davclient.get_fetchedEvents()

    if request.method == "POST":
        saveexcel = False

        for name, value in request.form.items():
            updateneeded = False
            event_uid = name.split("#")[0]  # das muss noch geändert werden ..

            if event_uid == "csrf_token":
                continue
            # print(name, value, event_uid)
            if davclient.set_eventCursorfromUID(event_uid) is None:
                flash(event_uid + u" nicht gültig", "danger")
                return redirect(url_for("index"))

            if value == "accept":
                attendee = davclient.find_attendee(name.split(":")[1])
                attendee.params["PARTSTAT"][0] = "ACCEPTED"
                attendee.params["ROLE"][0] = "REQ-PARTICIPANT"
                updateneeded = True

            if value == "promote":
                attendee = davclient.find_attendee(name.split(":")[1])
                attendee.params["PARTSTAT"][0] = "ACCEPTED"
                attendee.params["ROLE"][0] = "CHAIR"
                updateneeded = True

            if value == "delete":
                attendee = davclient.find_attendee(name.split(":")[1])
                attendee.params["ROLE"][0] = "NON-PARTICIPANT"
                updateneeded = True

            if value == "finalize":
                davclient.set_status("CONFIRMED")
                davclient.change_category(finalisieren, anfrageabgeschlossen)
                updateneeded = True

            if value == "abrechnen":
                if not saveexcel:
                    date_format = xlwt.XFStyle()
                    date_format.num_format_str = "dd.MM.yyyy hh:mm"

                    response = Response()
                    response.status_code = 200
                    workbook = xlwt.Workbook()
                    sheet = workbook.add_sheet("BSW Abrechnung")
                    ind = 0
                    writexlsheader(sheet, ind)
                saveexcel = True
                davclient.change_category(durchgefuehrt, abgerechnet)
                updateneeded = True
                startdatum = davclient.get_eventStart(string=False)
                dauer = davclient.get_eventDuration()
                insgesamt = dauer + timedelta(seconds=3600)

                for attendee in davclient.get_attendeeList():
                    if (
                        attendee.params["ROLE"][0] == "REQ-PARTICIPANT"
                        or attendee.params["ROLE"][0] == "CHAIR"
                    ):
                        """
                    # persons = []
                    # emailfound = Email.query.filter_by(
                    #     eadress=attendee[u"email"]
                    # ).all()
                    # for entry in emailfound:
                    #     persons.append(entry.persons)

                    # for pl in persons:
                    #     for p in pl:
                    """
                        ind = ind + 1
                        sheet.write(ind, 0, davclient.get_eventSummary())
                        sheet.write(
                            ind,
                            1,
                            startdatum.replace(tzinfo=None),
                            date_format,
                        )
                        if "," in attendee.params["CN"][0]:
                            name, vorname = attendee.params["CN"][0].split(",")
                        else:
                            vorname, name = attendee.params["CN"][0].split(" ")
                        sheet.write(ind, 2, name)
                        sheet.write(ind, 3, vorname)
                        #         a = p.adressen.filter_by(typ="Privat").first()
                        #         if a:
                        #             sheet.write(
                        #                 ind, 4, a.strasse + " " + str(a.hausnr)
                        #             )
                        #             sheet.write(ind, 5, a.plz)
                        #             sheet.write(ind, 6, a.ort)
                        #         a = p.anschluesse.filter_by(typ="Privat").first()
                        #         if a:
                        #             sheet.write(
                        #                 ind, 7, str(a.phonenr.international)
                        #             )
                        #         a = p.anschluesse.filter_by(
                        #             typ="Mobil-privat"
                        #         ).first()
                        #         if a:
                        #             sheet.write(
                        #                 ind, 8, str(a.phonenr.international)
                        #             )
                        sheet.write(ind, 9, attendee.value.split(":")[1])
                        sheet.write(ind, 10, "Unbekannt")
                        sheet.write(ind, 11, "Unbekannt")
                        sheet.write(ind, 12, str(dauer))
                        sheet.write(ind, 13, str(insgesamt))

            if updateneeded:
                event = davclient.get_currentEvent()
                event.save()

        if saveexcel:
            output = BytesIO()
            workbook.save(output)
            filename = "export.xls"
            response.data = output.getvalue()
            mimetype_tuple = mimetypes.guess_type(filename)
            response_headers = Headers(
                {
                    "Pragma": "public",
                    "Expires": "0",
                    "Cache-Control": "must-revalidate, post-check=0,"
                    + " pre-check=0",
                    "Cache-control": "private",
                    "Content-Type": mimetype_tuple[0],
                    "Content-Disposition": 'attachment; filename="%s";'
                    % filename,
                    "Content-Transfer-Encoding": "binary",
                    "Content-Length": len(response.data),
                }
            )

            if not mimetype_tuple[1] is None:
                response.update({"Content-Encoding": mimetype_tuple[1]})

            response.headers = response_headers
            response.set_cookie("fileDownload", "true", path="/")
            return response

        return redirect(
            url_for(
                "bsw_pages.bswreview", months=months, jetztdatumin=jetztdatumin
            )
        )

    for id, entry in enumerate(events):
        davclient.set_eventCursor(id)
        updateneeded = False

        if imonths < 0:
            for attendee in davclient.get_attendeeList():
                if "PARTSTAT" in attendee.params.keys():
                    if "ACCEPTED" not in attendee.params["PARTSTAT"]:
                        updateneeded = True
                        attendee.params["PARTSTAT"][0] = "ACCEPTED"

                    # Count number of BSW's already attended
                if attendee.value.split(":")[1] in bswAttendeeCount:
                    bswAttendeeCount[attendee.value.split(":")[1]] += 1
                else:
                    bswAttendeeCount[attendee.value.split(":")[1]] = 1

            for category in [anfrage, finalisieren, anfrageabgeschlossen]:
                if davclient.delete_category(category):
                    updateneeded = True
            if (not davclient.test_category(durchgefuehrt)) and (
                not davclient.test_category(abgerechnet)
            ):
                davclient.add_uniqueCategory(durchgefuehrt)
                updateneeded = True
        else:
            attendeeCount = 0
            form = BSWAddForm()
            bedarf = form.bedarf.data
            category_list = davclient.get_categoryList()
            for cl in category_list:
                for c in cl.value:
                    if "Bedarf=" in c:
                        bedarf = int(c.split("=")[1])

            for attendee in davclient.get_attendeeList():
                if "PARTSTAT" in attendee.params.keys():
                    if attendee.params["PARTSTAT"][0] == "DECLINED":
                        davclient.delete_attendee(attendee)
                        updateneeded = True
                    if attendee.params["PARTSTAT"][0] == "ACCEPTED":
                        attendeeCount += 1

            if davclient.test_category(anfrage):
                if attendeeCount >= bedarf:
                    davclient.change_category(anfrage, finalisieren)
                    updateneeded = True

            if davclient.test_category(finalisieren):
                if attendeeCount >= bedarf:
                    for attendee in davclient.get_attendeeList():
                        if "PARTSTAT" in attendee.params.keys():
                            if (
                                attendee.params["PARTSTAT"][0]
                                == "NEEDS-ACTION"
                            ):
                                davclient.delete_attendee(attendee)
                                updateneeded = True
                else:
                    davclient.change_category(finalisieren, anfrage)
                    davclient.set_status("TENTATIVE")
                    updateneeded = True

            if davclient.test_category(anfrageabgeschlossen):
                if attendeeCount >= bedarf:
                    for attendee in davclient.get_attendeeList():
                        if "PARTSTAT" in attendee.params.keys():
                            if attendee.params["PARTSTAT"][0] == "TENTATIVE":
                                davclient.delete_attendee(attendee)
                                updateneeded = True
                else:
                    davclient.change_category(anfrageabgeschlossen, anfrage)
                    davclient.set_status("TENTATIVE")
                    updateneeded = True

        if updateneeded:
            event = davclient.get_currentEvent()
            event.save()

    return render_template(
        "bsw/BSW.html",
        events=events,
        user=current_user,
        months=imonths,
        jetztdatumin=jetztdatumin,
        terminStatus=terminStatus,
        anfrage=anfrage,
        anfrageabgeschlossen=anfrageabgeschlossen,
        finalisieren=finalisieren,
        durchgefuehrt=durchgefuehrt,
        abgerechnet=abgerechnet,
        datetime=datetime,
        enumerate=enumerate,
        davclient=davclient,
        statistik=bswAttendeeCount,
        management_form=BSWSearchForm(),
        nextcloud_calendar=current_app.config[nextcloud]
        + "apps/calendar/timeGridDay/",
        submitDef="bsw_pages.bswreview",
    )


@bsw_pages.route(
    "/add-event-members/<eventid>/<months>/<jetztdatumin>",
    methods=["GET", "POST"],
)
@bsw_pages.route(
    "/add-event-members/<eventid>/<months>", methods=["GET", "POST"]
)
@login_required
def addeventmembers(eventid, months, jetztdatumin=None):
    ldapclient = LdapClient(
        LDAP_SERVER, LDAP_BASEDN, current_user.dn, current_user.get_password()
    )
    if request.method == "POST":
        davclient = DavCalendar(
            url=current_app.config[nextcloud]
            + "remote.php/dav/"
            + "principals/users/"
            + current_user.vorname
            + "_"
            + current_user.nachname
            + "/",
            username=current_user.username,
            password=current_user.get_password(),
            calendarname=current_app.config[bswcalendar],
        )
        bsw_calendar = davclient.get_calendar()
        if bsw_calendar is None:
            flash(
                current_app.config[bswcalendar] + u" nicht zugreifbar",
                "danger",
            )
            return redirect(url_for("index"))

        davclient.fetch_eventbyUID(eventid)
        updateneeded = False
        for name, value in request.form.items():
            entry = name.split("#")[0]  # das muss noch geändert werden ..

            if entry == "csrf_token":
                continue

            if value == "listselect":
                memberlist = ldapclient.get_listMembers(
                    entry.split(",")[0].split("=")[1], entry.partition(",")[2]
                )

            if value == "groupselect":
                memberlist = ldapclient.get_groupMembers(
                    entry.split(",")[0].split("=")[1], entry.partition(",")[2]
                )

            if value == "attendeeselect":
                memberlist = [literal_eval(entry)]
            # print(memberlist)

            for (cn, mail) in memberlist:
                member = davclient.create_attendee(
                    cn, "INDIVIDUAL", "OPT-PARTICIPANT", "mailto:" + mail
                )
                davclient.add_uniqueAttendee(member)
                updateneeded = True

        if updateneeded:
            event = davclient.get_currentEvent()
            # print(event.data)
            event.save()

        return redirect(
            url_for(
                "bsw_pages.bswreview", months=months, jetztdatumin=jetztdatumin
            )
        )
    return render_template(
        "bsw/select_attendee_base.html",
        user=current_user,
        management_form=BSWSearchForm(),
        event_id=eventid,
        months=months,
        jetztdatumin=jetztdatumin,
        ldapclient=ldapclient,
        enumerate=enumerate,
        lists_base_dn="dc=lists," + LDAP_BASEDN,
        groups_base_dn="dc=groups," + LDAP_BASEDN,
    )


@bsw_pages.route(
    "/add-members/<eventid>/<months>/<entry>/<type>/<jetztdatumin>",
    methods=["GET", "POST"],
)
@bsw_pages.route(
    "/add-members/<eventid>/<months>/<entry>/<type>", methods=["GET", "POST"]
)
@login_required
def addmembers(eventid, months, entry, type, jetztdatumin=None):
    ldapclient = LdapClient(
        LDAP_SERVER, LDAP_BASEDN, current_user.dn, current_user.get_password()
    )
    return render_template(
        "bsw/select_attendee.html",
        user=current_user,
        management_form=BSWSearchForm(),
        event_id=eventid,
        months=months,
        jetztdatumin=jetztdatumin,
        ldapclient=ldapclient,
        enumerate=enumerate,
        entry=entry,
        type=type,
    )
