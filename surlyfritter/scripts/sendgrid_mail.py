

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='kester@gmail.com',
    to_emails='kester@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
try:
    key = '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'
    sg = SendGridAPIClient(key)
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as err:
    print(err.message)
