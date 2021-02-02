"""
Static file routes via Flask.
"""
#TODO: replace these with gcloud routing to static later

from . import app

@app.route('/robots.txt')
@app.route('/robots')
def robots():
    """ Robots.txt static file """
    return app.send_static_file('robots.txt')

@app.route('/resume')
def resume():
    """ Resume static file """
    return app.send_static_file('resume.html')

@app.route('/air')
def air():
    """ Resume air quality file """
    return app.send_static_file('air_quality.html')

@app.route('/naga')
def naga():
    """ Naga zoom links for linus """
    return app.send_static_file('zoom.html')

@app.route('/zoom')
def zoom():
    """ Zoom links now include Gael link, this route is just a synonym for /naga """
    return app.send_static_file('zoom.html')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """ iphone homescreen icon """
    return app.send_static_file('images/july4th.png')

