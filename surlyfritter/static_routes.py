"""
Static file routes via Flask.
"""
#TODO: replace these with gcloud routing to static later

from flask import redirect
from . import app

@app.route("/tour")
@app.route("/tourdecure")
@app.route("/tour_de_cure")
def tour_de_cure():
    return app.send_static_file("tour_de_cure.html")

@app.route("/tourdonate")
@app.route("/tourdecuredonate")
@app.route("/tour_de_cure_donate")
@app.route("/tourdonatedirect")
@app.route("/tourdecuredonatedirect")
@app.route("/tour_de_cure_donate_direct")
def tour_de_cure_donate():
    return redirect("https://donations.diabetes.org/site/Donation2?idb=504997804&df_id=22747&FR_ID=13455&mfc_pref=T&22747.donation=form1&PROXY_ID=15794662&PROXY_TYPE=20")

@app.route("/tourmap")
@app.route("/tourdecuremap")
@app.route("/tour_de_cure_map")
@app.route("/deliverymap")
@app.route("/delivery_map")
@app.route("/tour_de_cure_delivery_map")
@app.route("/tourmap/<int:travel_time>")
@app.route("/tourdecuremap/<int:travel_time>")
@app.route("/tour_de_cure_map/<int:travel_time>")
@app.route("/deliverymap/<int:travel_time>")
@app.route("/delivery_map/<int:travel_time>")
@app.route("/tour_de_cure_delivery_map/<int:travel_time>")
def tour_de_cure_map(travel_time=70):
    return redirect(f"https://app.traveltime.com/search/0-lng=-122.2807966&0-lat=37.8542692&0-tt={travel_time}&0-mode=cycling-ferry&0-title=Team%20Amyris%20Goodies%20Zone")

@app.route("/pcpg")
def strava_purecane_pure_gain_club():
    return redirect("https://donations.diabetes.org/site/TR/TourdeCure/TourAdmin;jsessionid=00000000.app20043b?pg=team&fr_id=13306&team_id=755425&NONCE_TOKEN=28A04A598E539E0D9360C55304E3A8AD")

@app.route("/xmas-music")
@app.route("/music/xmas")
def spotify_xmas_music_playlist():
    return redirect("https://open.spotify.com/playlist/455y6U6A6GIytM2fIEnkyk?si=d4a8ddf070ca42d9")

@app.route("/music/xmas/jazz")
def spotify_xmas_jazz_music_playlist():
    return redirect("https://open.spotify.com/playlist/21d8tozBb2VYFWc6HUk6ci?si=f147829b6b474797")

@app.route("/music/xmas/bagpipes")
def spotify_xmas_bagpipes_music_playlist():
    return redirect("https://open.spotify.com/playlist/2HenJ53CnBDHXcseLrW9Md?si=f70adea369c84ea6")

@app.route("/images/recipes/<string:img_name>")
def images_recipes_static(img_name:str):
    """Recipes image endpoint"""
    recipes_img_name = f"recipes/{img_name}"
    print("images_recipes_static", img_name, recipes_img_name)
    return images_static(recipes_img_name)

@app.route("/images/<string:img_name>")
def images_static(img_name:str):
    """General image endpoint"""
    static_img = f"images/{img_name}"
    print("images_static", img_name, static_img)
    return app.send_static_file(static_img)

@app.route("/apple-touch-icon.png")
def apple_touch_icon():
    """iphone homescreen icon"""
    return app.send_static_file("images/july4th.png")
    
@app.route("/knuth")
def knuth():
    """Diamond hand-painted cat-crossing for Donald Knuth"""
    return redirect("https://photos.app.goo.gl/bYGjy9gQzdvDV7kT8")
