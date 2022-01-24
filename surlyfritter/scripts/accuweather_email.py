""" Get weather from AccuWeather and email it """

from datetime import datetime as dt
import sys

import requests
from sendgrid import SendGridAPIClient # https://github.com/sendgrid/sendgrid-python #pylint: disable=line-too-long
from sendgrid.helpers.mail import Mail

from python_http_client.exceptions import UnauthorizedError

# https://developer.accuweather.com/user/me/apps

PRECIP_KEYS = (
    "PrecipitationProbability",
    "PrecipitationIntensity",
    "PrecipitationType"
)
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S-08:00"

# Produce:
#
#        Today
#        Some sun, then clouds
#        H 63
#
#        Tonight
#        Clouds, a little rain late
#        L 50
#
TODAY_TMPL = """
        <br/>Today
        <br/>{description[Day]}; {description[Headline]}
        <br/>H {high:.0f}
        <br/>
        <br/>Tonight
        <br/>{description[Night]}
        <br/>L {low:.0f}
"""

# Produce:
#
#        Friday
#        Clouds giving way to some sun
#        H 60 / L 47
#
DAILY_TMPL = """
        <br/>{day}
        <br/>{description[Day]} then {description[night]}
        <br/>H {high:.0f} L {low:.0f}
"""

def get_url():
    """ Get the URL with app key for AccuWeather """
    with open("accuweather_key.txt") as key_file:
        app_key = key_file.readline().split(" ")[1].strip()

    base_url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/{}?apikey={}"
    #base_url = "http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{}?apikey={}"
    berkeley_location = "39625_PC"
    url = base_url.format(berkeley_location, app_key)
    return url

def send_email(headline, forecasts):
    """ Send the email """
    br_elem = "        <br/>"
    forecast_txt = br_elem.join(forecasts)
    body = "\n{}{br}\n{}{br}".format(headline, forecast_txt, br=br_elem)

    from_email = "kester@gmail.com"
    to_email = "kester@gmail.com"
    subject = "accuweather: {}".format(headline)
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body,
    )

    with open("accuweather_key.txt") as key_file:
        sendgrid_key = key_file.readline().split(" ")[1].strip()
    sendgrid = SendGridAPIClient(sendgrid_key)
    try:
        response = sendgrid.send(message)
        print(response)
    except UnauthorizedError as err:
        print("Sendmail error {}, printing report".format(err))
        print(forecast_txt.replace(br_elem, ""))

def _desc(forecast):
    """ Get the description of the day and precipitation message, if any """
    msg = ""
    if "HasPrecipitation" in forecast:
        for precip_key in PRECIP_KEYS:
            if precip_key in forecast:
                msg += forecast[precip_key]
    return "{} {}".format(forecast["IconPhrase"].strip(), msg.strip()).strip()

def parse_data(data):
    """ Get the forecast data out of AccuWeather's json """
    try:
        headline = data["Headline"]["Text"].strip()
    except KeyError as err:
        print("Error: {}\n{}".format(data["Message"], err))
        sys.exit(0)

    forecasts = []
    for i, daily in enumerate(data["DailyForecasts"]):
        day = dt.strptime(daily["Date"], DATE_FORMAT).strftime("%A")
        description = {t: _desc(daily[t]) for t in ("Day", "Night")}
        description["night"] = description["Night"].lower() # lower case for DAILY_TMPL
        description["Headline"] = headline # pack this here for TODAY_TMPL
        high = daily["Temperature"]["Maximum"]["Value"]
        low = daily["Temperature"]["Minimum"]["Value"]

        tmpl = DAILY_TMPL if i > 0 else TODAY_TMPL
        msg = tmpl.format(day=day, description=description, high=high, low=low)
        forecasts.append(msg)

    return headline, forecasts

def main():
    """ Get weather from AccuWeather and email it """
    resp = requests.get(get_url())
    data = resp.json()

    headline, forecasts = parse_data(data)
    send_email(headline, forecasts)

if __name__ == "__main__":
    main()
