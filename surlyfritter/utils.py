"""Utility functions for surlyfritter"""

import datetime
import dateutil.parser
import hashlib
import io
import os

from flask import session, render_template as flask_render_template
from PIL import Image, ExifTags
import requests

from sendgrid import SendGridAPIClient # https://github.com/sendgrid/sendgrid-python #pylint: disable=line-too-long
from sendgrid.helpers.mail import Mail

ADMIN_EMAILS = ['kester@gmail.com', 'apaske@gmail.com']

def get_key(name='sendgrid_key', filename='keys.txt'):
    """Get an entry from keys.txt"""
    site_root = os.path.realpath(os.path.dirname(__file__))
    file_url = os.path.join(site_root, filename)
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
        sendgrid = SendGridAPIClient(sendgrid_key)
        response = sendgrid.send(message)
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

def get_exif_data_from_url(img_url:str) -> datetime.datetime:
    """Extract the exif data of an image at img_url."""
    response = requests.get(img_url)
    img_file = io.BytesIO(response.content)
    return get_exif_data(img_file)

def get_exif_date_from_url(img_url:str) -> datetime.datetime:
    """Extract the exif date of the image at img_url."""
    response = requests.get(img_url)
    img_file = io.BytesIO(response.content)
    return get_exif_date(img_file)

def get_hash_from_url(img_url:str) -> str:
    """Extract the MD5 hash of the image at img_url."""
    #headers = {"Range": "bytes=0-100"}  # first 100 bytes
    #response = requests.get(img_url, headers=headers)
    #return response.content
    response = requests.get(img_url)
    hash_resp = hashlib.md5(response.content).hexdigest()
    return hash_resp

def get_exif_data(img_file) -> dict:
    """Extract the image's exif data and return as a human-readable dict."""
    with Image.open(img_file) as img:
        img_exif = img.getexif()

    if img_exif is None:
        print("no exif data in image")
        return img_exif

    # Stringify binaries for json serialization:
    img_exif_dict = dict()
    for key, value in img_exif.items():
        if key in ExifTags.TAGS:
            readable_key = ExifTags.TAGS[key]
        else:
            readable_key = str(key)
        img_exif_dict[readable_key] = str(value)

    return img_exif_dict

def get_exif_date(img_file) -> datetime.datetime:
    """Extract the date from the img_file's exif data."""
    # TODO: this doesn't do timezones correctly for some exif data

    # Sanity check on the magic _key numbers
    datetime_key = 306
    datetime_name = "DateTime"
    assert ExifTags.TAGS[datetime_key] == datetime_name

    #timezoneoffset_key = 34858
    #timezoneoffset_name = "TimeZoneOffset"
    #assert ExifTags.TAGS[timezoneoffset_key] == timezoneoffset_name

    #datetimeoriginal_key = 36867
    #datetimeoriginal_name = "DateTimeOriginal"
    #assert ExifTags.TAGS[datetimeoriginal_key] == datetimeoriginal_name

    img_exif = get_exif_data(img_file)
    if img_exif is None:
        print("no exif data in image")
        date = None
    else:
        date_str = img_exif.get(datetime_name, None)
        date = dateutil.parser.parse(date_str) if date_str is not None else None

    return date

#def string_to_date(date_str:str) -> datetime.datetime:
#    """
#    Try several formats to convert the date_str string into a datetime object.
#    """
#    if date_str is None:
#        return None
#
#    date_formats = [
#        '%Y:%m:%d %H:%M:%S',  # 2020:01:26 11:56:23
#        '%Y:%m:%d %H:%M:%SZ', # 2020:01:26 11:56:23Z
#        '%Y-%m-%d %H:%M:%S',  # 2020-01-26 11:56:23
#        '%Y-%m-%d %H:%M',     # 2020-01-26 11:56
#        '%Y-%m-%d',           # 2020-01-26
#        '%Y%m%d',             # 20200126
#        '%Y-%m',              # 2020-01
#        '%Y%m',               # 202001
#        '%Y',                 # 2020
#        '%Y %m %d %H:%M:%S',  # 2020 01 26 11:56:23
#        '%Y %m %d',           # 2020 01 26
#        '%Y %m',              # 2020 01
#        '%B %d, %Y',          # January 26, 2020
#        '%b %d %Y',           # Jan 26 2020
#        '%B %d, %Y',          # January 26, 2020
#        '%b %d %Y',           # Jan 26 2020
#        '%d %B %Y',           # 26 January 2020
#        '%d %b %Y',           # 26 Jan 2020
#        '%d %B, %Y',          # 26 January, 2020
#        '%d %b, %Y',          # 26 Jan, 2020
#        '%Y %d %B',           # 2020 26 January
#        '%Y %d %b',           # 2020 26 January
#    ]
#
#    date = None
#    for fmt in date_formats:
#        if date is None:
#            try:
#                date = datetime.datetime.strptime(date_str, fmt)
#            except ValueError as err:
#                print(err)
#    return date

def render_template(*args, **kwargs):
    """Render template with the user_img inserted into the render"""
    user_img = session.get('user_img')

    html = flask_render_template(
        *args, **kwargs,
        is_logged_in=is_logged_in(), user_img=user_img, is_admin=is_admin(),
    )
    return html
