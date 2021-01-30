
import datetime
import humanize

from . import app

@app.route('/quarantime')
def quarantime():
    march_13th = datetime.datetime(2020, 3, 13, 0, 0)
    march_31st = datetime.datetime(2020, 3, 31, 0, 0)
    now = datetime.datetime.now()
    td_13 = now - march_13th
    td_31 = now - march_31st
    day_of_march = humanize.ordinal(td_31.days+31)
    day_of_quarantine = humanize.ordinal(td_13.days)
    return f"""
    <html>
      <h1>
        It is March {day_of_march}, 
        the {day_of_quarantine} day of quarantine.
      </h1>
    </html>
"""
