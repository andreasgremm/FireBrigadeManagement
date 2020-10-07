# -*- coding: utf-8 -*-
from cryptography.fernet import Fernet
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from ldap3 import (
    ALL,
    SUBTREE,
    LEVEL,
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

from fwmanagement.formulare import LoginForm, ProfileForm
from fwmanagement.modelle import Benutzer, BenutzerEncoder
from Security.LDAP import (
    LDAP_BASEDN,
    LDAP_PASSWORD,
    LDAP_SERVER,
    LDAP_USER,
)

server = Server(LDAP_SERVER, get_info=ALL)


class CustomError(Exception):
    pass


admin_pages = Blueprint("admin_pages", __name__, template_folder="templates")


def ldapauth(uid, password):
    retrieveAttributes = ["mail", "cn", "sn", "givenName", "employeeType"]
    searchFilter = "(uid=" + uid + ")"

    try:
        conn = Connection(server, LDAP_USER, LDAP_PASSWORD, auto_bind=True)
        conn.search(
            search_base=LDAP_BASEDN,
            search_scope=SUBTREE,
            search_filter=searchFilter,
            attributes=retrieveAttributes,
        )
        if conn.response == []:
            return dict(error=True, message="LDAP - Ergebnis ist leer")
        else:
            if conn.response[0]["type"] == "searchResEntry":
                userdn, userattr = (
                    conn.response[0]["dn"],
                    conn.response[0]["attributes"],
                )

        # Authenticate final user
        conn.rebind(user=userdn, password=password)
        if not conn.bound:
            raise CustomError("User or Password not valid")
        conn.search(
            search_base=userdn,
            search_scope=SUBTREE,
            search_filter=searchFilter,
            attributes=retrieveAttributes,
        )
        if conn.response == []:
            return dict(error=True, message="LDAP - Ergebnis ist leer")
        else:
            if conn.response[0]["type"] == "searchResEntry":
                userdn, userattr = (
                    conn.response[0]["dn"],
                    conn.response[0]["attributes"],
                )
        conn.unbind()
    except Exception as e:
        conn.unbind()
        return dict(error=True, message=e)

    return dict(
        userdn=userdn,
        userattr=userattr,
        error=False,
    )


@admin_pages.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        authsuccess = ldapauth(username, password)
        # print(authsuccess, flush=True)
        if authsuccess["error"]:
            flash("Benutzername oder Passwort falsch", "danger")
        else:
            # print(authsuccess)
            id = authsuccess["userattr"]["mail"][0]
            registered_user = Benutzer(
                username,
                password,
                id,
                authsuccess["userattr"]["mail"][0],
                authsuccess["userattr"]["givenName"][0],
                authsuccess["userattr"]["sn"][0],
                authsuccess["userattr"]["employeeType"],
                authsuccess["userdn"],
            )
            login_user(registered_user, remember=form.remember_me.data)
            session["username"] = username
            # print(BenutzerEncoder().encode(registered_user))
            session[id] = BenutzerEncoder().encode(registered_user)
            session.permanent = not form.remember_me.data
            flash("Logged in successfully", "success")
            return redirect(request.args.get("next") or url_for("index"))

    return render_template(
        "/admin/login.html", form=form, title="Login", user=current_user
    )


@admin_pages.route("/change_profile", methods=["GET", "POST"])
@login_required
def profile():
    with Connection(
        server, current_user.dn, current_user.get_password(), auto_bind=True
    ) as conn:
        person = ObjectDef(["inetOrgPerson"], conn)
        r = Reader(conn, person, current_user.dn)
        r.search()
        # print(r[0].entry_attributes_as_dict)

    form = ProfileForm(request.form, obj=current_user)
    if request.method == "POST" and form.validate():
        w = Writer.from_cursor(r)
        # print(w[0].entry_attributes_as_dict)
        current_user.email = form.email.data
        current_user.vorname = form.vorname.data
        current_user.nachname = form.nachname.data
        w[0].givenName = current_user.vorname
        w[0].sn = current_user.nachname
        w[0].mail = current_user.email
        result = w[0].entry_commit_changes(refresh=True, controls=None)
        if result:
            flash(u"Profiländerung erfolgreich", "success")
            return redirect(url_for("index"))
        else:
            flash(u"Profiländerung nicht erfolgreich", "danger")
    return render_template(
        "/admin/changeprofile.html",
        form=form,
        user=current_user,
        title=u"Profiländerung",
    )


@admin_pages.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    session.pop(g.user.id, None)
    logout_user()
    return redirect(url_for("index"))
