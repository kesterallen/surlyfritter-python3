"""How long has quarantine been going on now?"""

import datetime
import humanize
import math

from surlyfritter.utils import string_to_date

from . import app

@app.route('/quarantime')
def quarantime():
    """Quarantine calendar"""
    march_1st = datetime.datetime(2020, 3,  1, 0, 0)
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

@app.route('/brimley/<dob_str>')
@app.route('/brimleyline/<dob_str>')
@app.route('/brimley_line/<dob_str>')
@app.route('/brimley-line/<dob_str>')
def brimley_line(dob_str:str):
    BRIMLEY_DAYS = 18530

    now = datetime.datetime.now()
    dob = string_to_date(dob_str)
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

@app.route('/pi_day')
@app.route('/pi-day')
@app.route('/piday')
def pi_day_route(piday_month=3, piday_dom=14):
    now = datetime.datetime.now()

    if piday_month == 3 and piday_dom == 14:
        glyph = "π"
    elif piday_month == 6 and piday_dom == 28:
        glyph = "τ"
    else:
        glyph = f"{piday_month}-{piday_dom}"

    if now.month == piday_month and now.day == piday_dom:
        msg = ""
    else:
        now_day = float(f"{now.month:02d}.{now.day:02d}")
        pi_day_ratio = now_day / (piday_month + piday_dom/100.0)
        msg = f"{pi_day_ratio:.3f} "

    return f"""
    <html>
      <h1>
        Happy {msg}{glyph} Day!
      </h1>
    </html>
    """
@app.route('/tau_day')
@app.route('/tau-day')
@app.route('/tauday')
def tau_day_route(piday_month=6, piday_dom=28):
    return pi_day_route(piday_month, piday_dom)
