
import datetime
import io
import os

from flask import session, render_template as flask_render_template
from PIL import Image, ExifTags
import requests

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

ADMIN_EMAILS = ['kester@gmail.com', 'apaske@gmail.com']

def get_key(name='sendgrid_key', filename='keys.txt'):
    """ Get an entry from keys.txt """
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    file_url = os.path.join(SITE_ROOT, filename)
    with open(file_url) as file:
        keys = file.readlines()
        for line in keys:
            line_name, value = line.split('=')
            if name == line_name:
                return value.strip()
    return None

def send_email(subject, body, to_email=ADMIN_EMAILS[0], from_email=ADMIN_EMAILS[0]):
    """ 
    Send an email
    https://app.sendgrid.com/settings/sender_auth/verify?link=2052482&domain=10170929&provider=Google%20Cloud
    """
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body,
    )
    try:
        sendgrid_key = get_key('sendgrid_key')
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as err:
        print(err)

def is_logged_in() -> bool:
    """Is there a user logged in"""
    entries = ['user_img', 'user_email', 'user_name']
    return all([e in session and session[e] is not None for e in entries])

def is_admin() -> bool:
    """Is there a user logged in with admin privs?"""
    return(is_logged_in() and
        session.get('user_email') in ADMIN_EMAILS)

def get_exif_date_from_url(img_url:str) -> datetime.datetime:
    """Extract the data from of the image at img_url from its exif data."""
    # TODO: probably a better way to do this
    response = requests.get(img_url)
    img_file = io.BytesIO(response.content)
    return get_exif_date(img_file) 

def get_exif_date(img_file) -> datetime.datetime:
    """Extract the data from the img_file's exif data."""
    DATETIME_KEY = 306
    assert ExifTags.TAGS[DATETIME_KEY] == "DateTime"

    # TODO: try this with context manager
    img = Image.open(img_file)
    img_exif = img.getexif()
    img_file.close()

    if img_exif is None:
        print("no exif data in image")
        date_str = None
    else:
        img_exif_dict = dict(img_exif)
        if DATETIME_KEY in img_exif_dict:
            date_str = img_exif_dict[DATETIME_KEY]
        else:
            print("no datetime field in image's exif data")
            date_str = None

    strptime_fmts = [ "%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M:%SZ", ]
    date = string_to_date(date_str, strptime_fmts)
    return date

def string_to_date(date_str:str, fmts) -> datetime.datetime:
    """ 
    Try several formats to convert the date_str string into a datetime object .
    """
    if date_str is None:
        return None

    date = None
    for fmt in fmts:
        if date is None:
            try:
                date = datetime.datetime.strptime(date_str, fmt)
            except ValueError as err:
                print(err)
    return date

def render_template(*args, **kwargs):
    """Render template with the user_img inserted into the render"""
    user_img = session.get('user_img')

    html = flask_render_template(*args, **kwargs,
        is_logged_in=is_logged_in(), user_img=user_img, is_admin=is_admin())
    return html
