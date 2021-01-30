
import os
from flask import session, render_template as flask_render_template

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

def render_template(*args, **kwargs):
    """Render template with the user_img inserted into the render"""
    user_img = session.get('user_img')

    html = flask_render_template(*args, **kwargs,
        is_logged_in=is_logged_in(), user_img=user_img, is_admin=is_admin())
    return html
