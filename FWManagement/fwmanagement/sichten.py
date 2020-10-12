# -*- coding: iso-8859-1 -*-
import json
import mimetypes
from io import BytesIO

import xlwt
from cryptography.fernet import Fernet
from flask import (
    Response,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.datastructures import Headers

# from ldaptools import app
from fwmanagement import app, login_manager
from fwmanagement.formulare import PersonSearchForm
from fwmanagement.modelle import Benutzer


def set_query_value(invalue):
    if len(invalue) > 0:
        result = "%" + invalue + "%"
    else:
        result = "%"
    return result


@login_manager.user_loader
def load_user(userid):
    reguser = json.loads(session[userid])
    return Benutzer(
        reguser["username"],
        Benutzer.decrypt_password(reguser["temp"]),
        reguser["id"],
        reguser["email"],
        reguser["vorname"],
        reguser["nachname"],
        reguser["employeeType"],
        reguser["dn"],
        reguser["principal"],
        reguser["calendarHost"],
        reguser["bswCalendar"],
    )


@app.before_request
def before_request():
    g.user = current_user


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title="Home", user=current_user)


@app.route("/all-links", endpoint="all-links")
# @login_required
def all_links():
    links = []
    for rule in app.url_map.iter_rules():
        url = rule.rule
        links.append((url, rule.endpoint))
    return render_template("all_links.html", links=links)


@app.route("/reports")
@login_required
def reports():
    return render_template(
        "reports.html",
        title="Berichte",
        user=current_user,
        management_form=PersonSearchForm(),
    )


@app.route("/simple-export")
@login_required
def simpleexport():
    response = Response()
    response.status_code = 200
    workbook = xlwt.Workbook()
    # code
    sheet = workbook.add_sheet("Andreas")
    style = xlwt.easyxf("font: bold 1")
    sheet.write(0, 0, "foobar", style)

    output = BytesIO()
    workbook.save(output)
    response.data = output.getvalue()
    filename = "export.xls"
    mimetype_tuple = mimetypes.guess_type(filename)

    response_headers = Headers(
        {
            "Pragma": "public",
            "Expires": "0",
            "Cache-Control": "must-revalidate, post-check=0, pre-check=0",
            "Cache-control": "private",
            "Content-Type": mimetype_tuple[0],
            "Content-Disposition": 'attachment; filename="%s";' % filename,
            "Content-Transfer-Encoding": "binary",
            "Content-Length": len(response.data),
        }
    )

    if not mimetype_tuple[1] is None:
        response.update({"Content-Encoding": mimetype_tuple[1]})
    response.headers = response_headers
    response.set_cookie("fileDownload", "true", path="/")
    print(response)
    return response
