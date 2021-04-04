"""
Static file routes via Flask.
"""
#TODO: replace these with gcloud routing to static later

from flask import redirect
from . import app

@app.route('/robots.txt')
@app.route('/robots')
def robots():
    """Robots.txt static file"""
    return app.send_static_file('robots.txt')

@app.route('/resume')
def resume():
    """Resume static file"""
    return app.send_static_file('resume.html')

@app.route('/air')
def air():
    """Resume air quality file"""
    return app.send_static_file('air_quality.html')

@app.route('/naga')
def naga():
    """Naga zoom links for linus"""
    return app.send_static_file('zoom.html')

@app.route('/zoom')
def zoom():
    """Zoom links now include Gael link, this route is just a synonym for /naga"""
    return app.send_static_file('zoom.html')

@app.route('/tour')
@app.route('/tourdecure')
@app.route('/tour_de_cure')
def tour_de_cure():
    return app.send_static_file('tour_de_cure.html')

@app.route('/tourdonate')
@app.route('/tourdecuredonate')
@app.route('/tour_de_cure_donate')
def tour_de_cure_donate():
    return redirect("http://main.diabetes.org/goto/kester")

@app.route('/tourmap')
@app.route('/tourdecuremap')
@app.route('/tour_de_cure_map')
@app.route('/deliverymap')
@app.route('/delivery_map')
@app.route('/tour_de_cure_delivery_map')
@app.route('/tourmap/<int:travel_time>')
@app.route('/tourdecuremap/<int:travel_time>')
@app.route('/tour_de_cure_map/<int:travel_time>')
@app.route('/deliverymap/<int:travel_time>')
@app.route('/delivery_map/<int:travel_time>')
@app.route('/tour_de_cure_delivery_map/<int:travel_time>')
def tour_de_cure_map(travel_time=70):
    return redirect(f"https://app.traveltime.com/search/0-lng=-122.2807966&0-lat=37.8542692&0-tt={travel_time}&0-mode=cycling-ferry&0-title=Team%20Amyris%20Goodies%20Zone")

@app.route('/images/<string:img_name>')
def images_static(img_name:str):
    """General image endpoint"""
    return app.send_static_file(f'images/{img_name}')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """iphone homescreen icon"""
    return app.send_static_file('images/july4th.png')
    
