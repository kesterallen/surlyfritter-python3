"""How long has quarantine been going on now?"""

import datetime
import dateutil.parser
import humanize
import math

from . import app


@app.route("/quarantime")
def quarantime():
    """Quarantine calendar"""
    march_1st = datetime.datetime(2020, 3, 1, 0, 0)
    march_13th = datetime.datetime(2020, 3, 13, 0, 0)
    now = datetime.datetime.now()
    td_13 = now - march_13th
    td_31 = now - march_1st
    day_of_march = humanize.ordinal(td_31.days)
    day_of_quarantine = humanize.ordinal(td_13.days)
    return f"""
    <html>
      <h1 style="text-align: center">
        It is March {day_of_march}, 2020:
        the {day_of_quarantine} day of quarantine
        <!-- (<a href="https://www.wunderground.com/maps/temperature/feels-like">feels like</a> day <a href="https://twitter.com/AgnesCallard/status/1358104983909134337">4,989,384</a>) -->.
      </h1>
    </html>
"""


@app.route("/brimley/<dob_str>")
@app.route("/brimleyline/<dob_str>")
@app.route("/brimley_line/<dob_str>")
@app.route("/brimley-line/<dob_str>")
def brimley_line(dob_str: str):
    BRIMLEY_DAYS = 18530

    now = datetime.datetime.now()
    dob = dateutil.parser.parse(dob_str)
    td = now - dob
    is_past_line = td.days > BRIMLEY_DAYS
    msg = "is" if is_past_line else "is not"

    return f"""
    <html>
      <h1>
        {dob_str} {msg} past the Brimley/Cocoon Line
      </h1>
    </html>
    """


@app.route("/pi_day")
@app.route("/pi-day")
@app.route("/piday")
def pi_day_route(month: int = 3, day: int = 14):
    """Is it Pi-Day?"""

    def _nowratio(month: int, day: int) -> float:
        """Goofy decimal date ratio between "now" and pi day's month.day"""
        now = datetime.datetime.now()
        if now.month == month and now.day == day:
            return 1  # distrust floating point division
        return (now.month + now.day / 100.0) / (month + day / 100.0)

    is_pi = (month, day) == (3, 14)
    is_tau = (month, day) == (6, 28)
    mode = "π" if is_pi else "τ" if is_tau else f"{month}-{day}"

    # If it's Pi day, celebrate! Otherwise present the fractional result.
    ratio = _nowratio(month, day)
    msg = " " if ratio == 1 else f" {ratio:.3f} "

    return f"<html><h1>Happy{msg}{mode} Day!</h1></html>"


@app.route("/tau_day")
@app.route("/tau-day")
@app.route("/tauday")
def tau_day_route(month: int = 6, day: int = 28):
    """This one's for you, Colin"""
    return pi_day_route(month, day)
