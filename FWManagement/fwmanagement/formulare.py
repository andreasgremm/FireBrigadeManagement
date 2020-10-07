import datetime as dt

from flask_wtf import FlaskForm as Form
from wtforms import (
    BooleanField,
    FileField,
    HiddenField,
    PasswordField,
    RadioField,
    SelectField,
    TextAreaField,
    TextField,
    validators,
)
from wtforms.validators import DataRequired, Optional, Regexp, ValidationError

from wtforms_components import (
    DateField,
    DateTimeField,
    EmailField,
    If,
    IntegerField,
)

my_date_format = "%Y-%m-%d"
my_date_format1 = "%d.%m.%Y %H:%M"


def checkfile(form, field):
    if field.data:
        filename = field.data.filename.lower()
        ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])
        if not (
            "." in filename
            and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS
        ):
            raise ValidationError(
                "Falscher Dateityp, es sind nur png,jpg,jpeg,gif Dateien erlaubt."
            )


class LoginForm(Form):
    username = TextField("Benutzername", [validators.Length(min=4, max=25)])
    password = PasswordField("Passwort", [validators.Length(min=8, max=40)])
    remember_me = BooleanField("Eingeloggt bleiben", default=False)


class ProfileForm(Form):
    email = TextField(
        "Emailadresse",
        validators=[
            validators.Email(message=u"Keine gültige Emailadresse"),
            validators.Length(min=6, max=35),
        ],
    )
    vorname = TextField("Vorname", validators=[validators.DataRequired()])
    nachname = TextField("Nachname", validators=[validators.DataRequired()])


class PersonBaseForm(Form):
    pid = HiddenField("")
    vorname = TextField("Vorname", [validators.Required()])
    name = TextField("Nachname", [validators.Required()])
    title = TextField("Titel")
    birthday = DateField(
        "Geburtstag (tt.mm.jjjj)",
        [validators.Required()],
        format=my_date_format,
    )


class PersonSelfserviceForm(PersonBaseForm):
    arbeitgeber = TextField("Arbeitgeber")
    abteilung = TextField("Abteilung")
    taetigkeit = TextField(u"Tätigkeit")
    angehoeriger = TextAreaField(u"Angehöriger")


class PersonBildForm(Form):
    bild = FileField("Bild", validators=[checkfile])


class PersonAdressSearchForm(Form):
    name = TextField("Vorname")
    surname = TextField("Nachname")
    title = TextField("Titel")
    strasse = TextField("Strasse")
    hausnr = TextField("Hausnummer")
    plz = TextField("PLZ")
    ort = TextField("Ort")


class PersonSearchForm(Form):
    name = TextField(
        "Vorname oder Nachname",
        [validators.DataRequired()],
        description="Beschreibung",
    )


class BSWSearchForm(Form):
    ddatum = DateField('BSW (yyyy-mm-tt)', [validators.Required()],
                format=my_date_format)
    monate = IntegerField(label="Monate", default=0)


class BSWAddForm(Form):
    sdatum = DateTimeField('Anfang (tt.mm.yyyy hh:mm)', [validators.Required()],
                           format=my_date_format1)
    edatum = DateTimeField('Ende (tt.mm.yyyy hh:mm)', [validators.Required()],
                           format=my_date_format1)
    location = TextField(u"Ort", [validators.Required()])
    summary = TextField(u"Titel", [validators.Required()])
    beschreibung = TextAreaField(u"Beschreibung", [validators.Required()])
    bedarf = IntegerField(u"Teilnehmer-Bedarf", default=2)
