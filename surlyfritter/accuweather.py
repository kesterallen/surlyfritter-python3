""" Get weather from AccuWeather and email it """

from datetime import datetime as dt
import sys

import requests
from sendgrid import SendGridAPIClient # https://github.com/sendgrid/sendgrid-python #pylint: disable=line-too-long
from sendgrid.helpers.mail import Mail

from python_http_client.exceptions import UnauthorizedError

from . import app
from flask import current_app

# https://developer.accuweather.com/user/me/apps

PRECIP_KEYS = (
    "PrecipitationProbability",
    "PrecipitationIntensity",
    "PrecipitationType"
)
DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S-08:00", "%Y-%m-%dT%H:%M:%S-07:00"]

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
        <br/>{description[Day]}
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
    with current_app.open_resource("static/accuweather_key.txt") as key_file:
        app_key = key_file.readline().split(b" ")[1].strip().decode("utf-8")

    base_url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/{}?apikey={}"
    berkeley_location = "39625_PC"
    url = base_url.format(berkeley_location, app_key)
    return url

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
        for DATE_FORMAT in DATE_FORMATS:
            try:
                day = dt.strptime(daily["Date"], DATE_FORMAT).strftime("%A")
            except ValueError:
                pass
        description = {t: _desc(daily[t]) for t in ("Day", "Night")}
        description["night"] = description["Night"].lower() # lower case for DAILY_TMPL
        description["Headline"] = headline # pack this here for TODAY_TMPL
        high = daily["Temperature"]["Maximum"]["Value"]
        low = daily["Temperature"]["Minimum"]["Value"]

        tmpl = DAILY_TMPL if i > 0 else TODAY_TMPL
        msg = tmpl.format(day=day, description=description, high=high, low=low)
        forecasts.append(msg)

    return headline, forecasts

@app.route('/accuweather')
def accuweather():
    """ Get weather from AccuWeather and email it """
    resp = requests.get(get_url())
    data = resp.json()

    headline, forecasts = parse_data(data)
    return "<h1>{}</h1>".format("<br/>".join(forecasts))

if __name__ == "__main__":
    main()
