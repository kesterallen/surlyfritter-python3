"""
Non-admin controllers for surlyfritter
"""

#TODO print --> logging

import datetime
import io
import os
import random
import re

from flask import redirect, request, send_file, abort
from google.cloud import storage
from google.cloud.exceptions import NotFound

from surlyfritter.models import (
    GCS_BUCKET_NAME,
    DAYS_IN_YEAR,
    DOB,
    Picture,
    Tag,
)
from surlyfritter.utils import (
    get_exif_data_from_url,
    get_exif_date,
    get_hash_from_url,
    render_template,
    send_email,
    string_to_date,
)

from . import app, client

@app.errorhandler(404)
def page_not_found(error):
    """Render a nice 404 page"""
    # Note 404 status is set explicitly
    return render_template('error_404.html', error=error), 404

@app.route('/imgperm/<int:added_order>')
@app.route('/imgp/<int:added_order>')
@app.route('/ip/<int:added_order>')
def image_perm(added_order:int):
    """
    Non-GCS (expensive!) image server.  Use this only if the GCS URL is
    unvailable.
    """
    with client.context():
        try:
            picture = Picture.query(Picture.added_order == added_order).get()
            if picture is None:
                print(f"""no Picture with .added_order of {added_order},
                    returning most recent""")
                picture = Picture.most_recent()

            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(picture.name)
            img = io.BytesIO(blob.download_as_bytes())
        except NotFound as err: # blob not found
            abort(404, f"blob for added_order={added_order} "
                f"not found in image_perm; {err}")

        return send_file(img, mimetype='image/jpeg')

@app.template_filter('shuffle')
def filter_shuffle(seq):
    """A shuffle filter for the template"""
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq

@app.template_filter('tag_fs_size')
def filter_tagfontsize(tag):
    """A tag font size fitler for the template"""
    try:
        result = int(6 - tag.tag_count_log)
        return result
    except:
        return 6

@app.route('/')
@app.route('/d')
@app.route('/d/<int:img_id>')
@app.route('/display')
@app.route('/display/<int:img_id>')
@app.route('/displayperm/<int:img_id>')
@app.route('/n')
@app.route('/nav')
@app.route('/nav/<int:img_id>')
@app.route('/navperm')
@app.route('/navperm/<int:img_id>')
@app.route('/n/<int:img_id>')
@app.route('/p/')
@app.route('/p')
@app.route('/perm/<int:img_id>')
@app.route('/picture/')
@app.route('/picture')
@app.route('/picture/<int:img_id>')
@app.route('/p/<int:img_id>')
@app.route('/<int:img_id>.jpg')
def display(img_id:int=None):
    """
    Display the picture that img_id == Picture.added_order for. If that doesn't
    exist, serve Picture.most_recent.
    """
    with client.context():
        if img_id is not None:
            picture = Picture.query(Picture.added_order == img_id).get()
        else:
            picture = Picture.most_recent()
        pictures = [picture] if picture is not None else None
        tags = Tag.query().fetch()

        html = render_template('display.html', pictures=pictures, tags=tags)
        return html

@app.route('/display/highest')
@app.route('/d/highest')
def display_highest():
    """Show the picture page for the picture with the most recent date"""
    with client.context():
        picture = Picture.most_recent()
    return redirect(f"/p/{picture.added_order}")

@app.route('/display/newest')
@app.route('/d/mostrecent')
@app.route('/display/highestp')
@app.route('/d/highestp')
def display_newest():
    """Show the picture page for the picture that was added most recently"""
    with client.context():
        picture = Picture.last_added()
    return redirect(f"/p/{picture.added_order}")

@app.route('/display/oldest')
@app.route('/d/oldest')
@app.route('/display/leastrecent')
@app.route('/d/leastrecent')
@app.route('/display/lowestp')
@app.route('/d/highestp')
def display_oldest():
    """Show the picture page for the oldest picture"""
    with client.context():
        picture = Picture.least_recent()
    return redirect(f"/p/{picture.added_order}")

@app.route('/random')
def random_page():
    """Load a random picture"""
    with client.context():
        num_pics = Picture.query().count()
        index = random.randrange(0, num_pics)
        return redirect(f"/p/{index}")

@app.route('/feed')
@app.route('/feed/<int:max_num>')
@app.route('/feeds/feed.xml')
def feed(max_num:int=5):
    """
    RSS feed for the most recent 'max_num' pictures.
    """
    with client.context():
        pictures = Picture.query().order(-Picture.added_order).fetch(max_num)
        return render_template('feed.xml', pictures=pictures)

@app.route('/tags/<tag_text>/all')
def pictures_for_tags_all(tag_text:str):
    """Display all pictures with the tag 'tag_text'"""
    return pictures_for_tags(tag_text=tag_text, max_num=None)

@app.route('/tags/<tag_text>/<int:max_num>')
@app.route('/tags/<tag_text>')
def pictures_for_tags(tag_text:str, max_num:int=5):
    """Display N pictures with the tag 'tag_text'"""
    with client.context():
        # Run a separate count in case the unfiltered Pictures array would be
        # large:
        total_count = Picture.with_tag_count(tag_text)
        pictures = Picture.with_tag(tag_text, num=max_num)
        return render_template('display.html', pictures=pictures,
            tag_text=tag_text, total_count=total_count)

def _kid_is(name:str, age_years:float):
    """Return a redirect the display page for kid 'name' at age 'age_years'"""
    with client.context():
        added_order= Picture.kid_is_index(name, age_years)
        return redirect(f"/p/{added_order}")

@app.route('/miri_is/<int:age_years>')
@app.route('/miri_is/<float:age_years>')
def miri_is(age_years:float):
    """Return a redirect the display page for miri at age 'age_years'"""
    return _kid_is('miri', age_years)

@app.route('/julia_is/<int:age_years>')
@app.route('/julia_is/<float:age_years>')
def julia_is(age_years:float):
    """Return a redirect the display page for julia at age 'age_years'"""
    return _kid_is('julia', age_years)

@app.route('/linus_is/<int:age_years>')
@app.route('/linus_is/<float:age_years>')
def linus_is(age_years:float):
    """Return a redirect the display page for linus at age 'age_years'"""
    return _kid_is('linus', age_years)

@app.route('/same-age/<int:age_years>')
@app.route('/same-age/<float:age_years>')
@app.route('/same-age')
def same_age(age_years=None):
    """Return a redirect the display page for linus at age 'age_years'"""
    if age_years is None:
        linus_age = datetime.datetime.now() - DOB['linus']
        age_years = random.uniform(0, linus_age.days / DAYS_IN_YEAR)
    with client.context():
        miri = Picture.kid_is_index('miri', age_years)
        julia = Picture.kid_is_index('julia', age_years)
        linus = Picture.kid_is_index('linus', age_years)
        return redirect(f"/sbs/{miri}/{julia}/{linus}")

@app.route('/side_by_side/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
@app.route('/sbs/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
@app.route('/display_multiple/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
@app.route('/multiple/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
@app.route('/dm/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
@app.route('/m/<int:img_id1>/<int:img_id2>/<int:img_id3>/')
def side_by_side(img_id1:int, img_id2:int, img_id3:int):
    """Display the three images on one page"""
    with client.context():
        pictures = [
            Picture.query(Picture.added_order == img_id1).get(),
            Picture.query(Picture.added_order == img_id2).get(),
            Picture.query(Picture.added_order == img_id3).get(),
        ]
        return render_template('display.html', pictures=pictures, side_by_side=True)

@app.route('/mm/<img_ids_str>')
def side_by_side_list(img_ids_str:str):
    """Display a list of images on one page"""
    img_ids = [int(i) for i in img_ids_str.split(",")]
    with client.context():
        pictures = []
        for img_id in img_ids:
            picture = Picture.query(Picture.added_order == img_id).get()
            pictures.append(picture)
        return render_template('display.html', pictures=pictures, side_by_side=True)

@app.route('/date/<date_str>')
def display_date(date_str:str):
    """
    Display the picture closest to 'date_str'
    """
    with client.context():
        date = string_to_date(date_str)
        if date is None:
            return f"The input date {date_str} is not a valid date"

        picture = Picture.from_date(date)
        return redirect(f"/p/{picture.imgp_id}")

@app.route('/timejump/<int:added_order>/<int(signed=True):years>')
@app.route('/timejump/<int:added_order>/<float(signed=True):years>')
@app.route('/tj/<int:added_order>/<int(signed=True):years>')
@app.route('/tj/<int:added_order>/<float(signed=True):years>')
def timejump(added_order:int, years:float):
    """Display the page for 'years' + the date of Picture.added_order"""
    with client.context():
        timejump_index= Picture.timejump_index(added_order, years)
        return redirect(f"/p/{timejump_index}")

@app.route('/picture/add', methods=['GET', 'POST'])
def picture_add():
    """
    Add one or more Picture/GCS blob pair(s), or render the template to upload
    new pictures. If it exists, use the EXIF date for the date, otherwise use
    'now'. Use 'now' for part of the filename.
    """
    if request.method == 'POST':
        # POST: upload picture(s)
        imgs = request.files.getlist("pictures")
        names = dict(success=[], fail=[])
        for img in imgs:
            try:
                now = datetime.datetime.now()
                (name, ext) = os.path.splitext(img.filename)
                name = f"{name}_{now.timestamp()}{ext}"
                picture = Picture.create(img, name)

                date = get_exif_date(img)
                if date is None:
                    date = now

                names['success'].append(name)
            except UnboundLocalError as err:
                names['fail'].append((name, err))

        status = "succeeded" if len(names['fail']) == 0 else "failed"
        message = f'''
            Your picture uploaded {status}. <br/>
            Successful uploads {names['success']}. <br/>
            Failed uploads {names['fail']}. <br/>
            <a href="/p/{picture.imgp_id}">See pictures</a>
        '''

        send_email(
            subject=f"Added: /p/{picture.imgp_id}",
            body=f"""
                Added picture {picture.img_url} (/p/{picture.imgp_id})
                {message}
            """
        )
        return redirect(f"/picture/add?message={message}")
    else:
        # GET: Render form with optional message
        message = request.args.get('message')
        return render_template('add.html', message=message)

@app.route('/tag/add', methods=['POST'])
def tag_add():
    """Add a tag to a picture"""
    tag_text_raw = request.values.get("tag_text")
    tag_texts = re.sub(r'[^,\w]', ' ', tag_text_raw).split(',')
    added_order = int(request.values.get("img_id"))

    with client.context():
        picture = Picture.query(Picture.added_order == added_order).get()
        for tag_text in tag_texts:
            tag_text = tag_text.lower().strip()
            picture.add_tag(tag_text)

    return redirect(f"/p/{added_order}")

@app.route('/comment/add', methods=['POST'])
def comment_add():
    """Add a comment to a picture"""
    comment_text = request.values.get("comment_text")
    added_order = int(request.values.get("img_id"))

    with client.context():
        picture = Picture.query(Picture.added_order == added_order).get()
        picture.add_comment(comment_text)

    return redirect(f"/p/{added_order}")

@app.route('/meta/<int:img_id>')
@app.route('/p/meta/<int:img_id>')
@app.route('/picture/meta/<int:img_id>')
def meta(img_id:int):
    """Display a Picture's metadata, by its .added_order attribute"""
    with client.context():
        picture = Picture.query(Picture.added_order == img_id).get()
        if picture is None:
            abort(404, f"No picture for ID {img_id}")
        return picture.meta

@app.route('/exif/<int:img_id>')
def exif(img_id:int):
    """Display a Picture's image exif metadata, by its .added_order attribute"""
    with client.context():
        picture = Picture.query(Picture.added_order == img_id).get()
        if picture is None:
            abort(404, f"No picture to get exif from for ID {img_id}")
        return get_exif_data_from_url(picture.img_url)

@app.route('/hash/<int:img_id>')
def hash(img_id:int):
    """Display a Picture's MD5 hash, by its .added_order attribute"""
    with client.context():
        picture = Picture.query(Picture.added_order == img_id).get()
        if picture is None:
            abort(404, f"No picture to get exif from for ID {img_id}")
        hash_value = get_hash_from_url(picture.img_url)
    return hash_value
