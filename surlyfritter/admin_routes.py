"""
Admin routes
"""

import datetime
import io
import pprint
import PIL.Image

import jwt
import requests
from flask import redirect, request, abort, session

from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests


from surlyfritter.models import Picture, Tag, Comment, GCS_BUCKET_NAME
from surlyfritter.utils import (
    send_email,
    render_template,
    get_key,
    is_logged_in,
    is_admin,
    get_exif_date_from_url,
    string_to_date,
)

from . import app, client

#TODO print --> logging (https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-to-cloud-logging)

def _counts():
    """Extract the count of pictures, blobs, tags, and comments"""
    with client.context():
        num_pics = Picture.query().count()
        num_tags = Tag.query().count()
        num_comments = Comment.query().count()

    num_blobs = 0
    storage_client = storage.Client()
    for _ in storage_client.list_blobs(GCS_BUCKET_NAME):
        num_blobs += 1

    return dict(
        pics=num_pics,
        blobs=num_blobs,
        tags=num_tags,
        comments=num_comments
    )

@app.route('/logout')
def logout():
    """ Clear session of user info to log out """
    session['user_img'] = None
    session['user_email'] = None
    session['user_name'] = None
    return redirect(request.referrer)

@app.route('/gauth', methods=['POST'])
def gauth():
    """
    Google Onetap auth handler
    https://developers.google.com/identity/sign-in/web/server-side-flow
    """
    # Exit early if already authenticated
    if is_logged_in():
        return redirect(request.referrer)

    # Valiidate tokens:
    csrf_token_cookie = request.cookies.get('g_csrf_token')
    if not csrf_token_cookie:
        abort(400, 'No CSRF token in Cookie.')

    csrf_token_body = request.values.get('g_csrf_token')
    if not csrf_token_body:
        abort(400, 'No CSRF token in post body.')

    if csrf_token_cookie != csrf_token_body:
        abort(400, 'Failed to verify double submit cookie.')

    # Get credential and set user info:
    credential = request.values.get('credential')
    decoded = jwt.decode(credential, options={"verify_signature": False})
    client_id = get_key('onetap_key')
    #decoded_token = jwt.decode(csrf_token_body, options={"verify_signature": False})
    #idinfo = id_token.verify_oauth2_token(decoded_token, g_requests.Request(), client_id)

    session['user_img'] = decoded['picture']
    session['user_email'] = decoded['email']
    session['user_name'] = decoded['name']
    return redirect(request.referrer)

@app.route('/counts')
def counts():
    """Display the count of pictures and blobs"""
    if not is_admin():
        abort(404, "counts is admin-only")

    counts_dict = _counts()
    return render_template('admin_report.html', counts=counts_dict)

# TODO: remove this
@app.route('/delete/all')
def delete_everything():
    """Erase everything"""
    # TODO: ask if user is sure before doing this

    abort(404, "delete-all is a disabled endpoint")

#    if not is_admin():
#        abort(404, "delete-all is admin-only")
#
#    deletes = dict(
#        blobs=[],
#        pictures=[],
#        tags=[],
#        comments=[],
#    )
#    with client.context():
#        for picture in Picture.query().iter():
#
#            try:
#                # Delete blob with picture.name
#                storage_client = storage.Client()
#                bucket = storage_client.bucket(GCS_BUCKET_NAME)
#                blob = bucket.blob(picture.name)
#                blob.delete()
#                deletes['blobs'].append(picture.name)
#            except:
#                deletes['blobs'].append(f"failure: {picture.name}")
#
#            try:
#                # Delete picture
#                picture.key.delete()
#                deletes['pictures'].append(picture.name)
#            except:
#                deletes['pictures'].append(f"failure: {picture.name}")
#
#        for tag in Tag.query().iter():
#            tag.key.delete()
#            deletes['tags'].append(tag.text)
#
#        for comment in Comment.query().iter():
#            comment.key.delete()
#            deletes['comments'].append(comment.text)
#
#    message = "Delete report:"
#    return render_template('admin_report.html', deletes=deletes, message=message)

@app.route('/picture/edit/<int:img_id>', methods=['GET', 'POST'])
def picture_edit(img_id:int):
    """ Edit a Picture that already exists """

    # TODO alter date
    # TODO remove comment or tag

    if not is_admin():
        abort(404, "edit is admin-only")

    with client.context():

        if request.method == 'POST':
            try:
                #img_id = int(request.form.get("img_id"))
                picture = Picture.query(Picture.added_order == img_id).get()
                if picture is None:
                    abort(404, f"Cannot find picture with added_order = {img_id}")

                # Make blob from file, if a file is supplied:
                img = request.files.get("picture")
                if img:
                    Picture.blob_create(img, picture.name)

                # Update rotation:
                img_rot_raw = request.form.get("img_rot")
                if img_rot_raw:
                    try:
                        img_rot = int(img_rot_raw) % 360
                    except ValueError:
                        abort(404, f"Bad image rotation request: {img_rot_raw}")
                    if img_rot % 90 == 0:
                        picture.img_rot = int(img_rot)

                # TODO: Alter .date:
                #
                new_date = request.form.get("new_date")
                if new_date:
                    date = string_to_date(new_date)
                    picture.date = date

                    # set prev_pic's .next_pic_ref to next_pic, if prev_pic exists (or None, if next_pic doesn't exist)
                    if picture.next_pic_ref:
                        picture.prev_pic.next_pic_ref = picture.next_pic.key

                    # set next_pic's .prev_pic_ref to prev_pic, if next_pic exists (or None, if prev_pic doesn't exist)
                    if picture.prev_pic_ref:
                        picture.next_pic.prev_pic_ref = picture.prev_pic.key

                    # set picture.next_pic_ref and picture.prev_pic_ref in the same way that Picture.create
                    prev_pic_key, next_pic_key = Picture.prev_next_pic_keys(date)
                    picture.prev_pic_ref = prev_pic_key
                    picture.next_pic_ref = next_pic_key

                picture.updated_on = datetime.datetime.now()
                picture.put()
            except NotFound as err: # blob not found
                abort(404, f"Blob with {picture.name} not found, exiting")

            return redirect(f"/p/{picture.imgp_id}")
        else:
            # GET: Render form with optional message
            picture = Picture.query(Picture.added_order == img_id).get()

            exif_date = get_exif_date_from_url(picture.img_url)


            if picture is None:
                abort(404, f"Cannot find picture with added_order = {img_id}")
            message = "Edit Mode"

            return render_template('add.html', message=message, 
                edit_picture=picture, exif_date=exif_date)

@app.route('/picture/delete/<int:img_id>')
def picture_delete(img_id:int):
    """
    Delete a Picture and its associated blob, by its .added_order attribute
    """
    if not is_admin():
        abort(404, "picture delete is admin-only")

    with client.context():
        try:
            picture = Picture.query(Picture.added_order == img_id).get()
            if picture is None:
                abort(404, f"Cannot find picture with added_order = {img_id}")
            picture_meta = picture.meta

            # delete blob with picture.name
            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(picture.name)
            blob.delete()
        except NotFound as err: # blob not found
            #abort(404, f"Blob with {picture.name} not found, exiting")
            pass

        # Update prev/next pointers on the adjacent pics, unless this is the
        # first/last image. If this is the first image, null the prev_pic_ref
        # pointer for the (new) first image If this is the lat image, null the
        # next_pic_ref pointer for the (new) last image
        #
        if picture.prev_pic_ref is not None:
            # 'picture' is not the first picture, nominal case
            prev_pic = picture.prev_pic
            prev_pic.next_pic_ref = picture.next_pic_ref
            prev_pic.put()
        else:
            # 'picture' is the first picture (prev_pic_ref is None), so set
            # the NEW first picture's (next_pic) prev pointer to None
            next_pic = picture.next_pic
            next_pic.prev_pic_ref = None
            next_pic.put()

        if picture.next_pic_ref is not None:
            # 'picture' is not the last picture, nominal case
            next_pic = picture.next_pic
            next_pic.prev_pic_ref = picture.prev_pic_ref
            next_pic.put()
        else:
            # If this is the last picture (prev_pic_ref is None), so set the
            # NEW last picture's (prev_pixc) next pointer to None
            prev_pic = picture.prev_pic
            prev_pic.next_pic_ref = None
            prev_pic.put()

        # delete picture
        picture.key.delete()

        send_email(subject=f'deleted picture {img_id}',
            body=f'deleted picture {img_id}')
        return f"deleted {img_id}:\n{picture_meta}"

@app.route('/import/hrd', methods=['POST'])
def import_hrd():
    """
    Import data from an HRD image's metadata JSON

    TODO: HRD import must be done in old site's added_order order to preserve
    added_order
    """
    abort(404, 'Import-HRD is disabled')

#    hrd_meta = request.get_json(force=True)
#
#    # Download image from old site:
#    try:
#        response = requests.get(hrd_meta['url']) # N.B. 'requestS' library
#        img = io.BytesIO(response.content)
#        now = datetime.datetime.now().timestamp()
#        added_order = hrd_meta['added_order']
#        name = f"hrd_import_{added_order}_{now}.jpg"
#        date = datetime.datetime.strptime(hrd_meta['date'], '%Y:%m:%d %H:%M:%S')
#
#        picture = Picture.create(img, name, date)
#
#        # Add comments and tags:
#        with client.context():
#            for tag in hrd_meta['tags']:
#                picture.add_tag(tag)
#            for comment in hrd_meta['comments']:
#                picture.add_comment(comment)
#    except:
#        abort(404, f'Import-HRD failure for {hrd_meta["url"]}')
#
#    return hrd_meta

@app.route('/fix-next-prev')
def fix_next_prev_links():
    """
    Fix next/prev links

    Fetch a list of Pictures with next_pic_ref is None. This is incorrect for
    every picture except the one that was added last. Remove Picture.last_added
    from list: the rest of the pictures in the list need repair. Update these
    to have next_pic_ref point to 'Picture.next_by_date(picture.date)'

    Fetch a list of Pictures with prev_pic_ref is None. This is incorrect for
    every picture except the one that was added first. Remove
    Picture.first_added from list: the rest of the pictures in the list need
    repair. Update these to have prev_pic_ref point to
    'Picture.prev_by_date(picture.date)'

    By default, pylint will complain in the Picture.query calls about the '==
    None' (it will reccomend 'is None' instead) syntax, but '== None' is the
    correct syntax for NDB cloud: thus the 'pylint: disable' pylint disable
    comment instructions.
    """
    if not is_admin():
        abort(404, "fix-next-prev is admin-only")

    fixes = dict(prev=[], next=[])
    def _report_entry(pic, target, report_key):
        meta = pic.meta
        meta.update(target=target.meta)
        fixes[report_key].append(meta)

    with client.context():

        most_recent_key = Picture.most_recent().key
        least_recent_key = Picture.least_recent().key

        # Fix broken next links
        broken_pics = Picture.query(Picture.next_pic_ref == None).iter() # pylint: disable=singleton-comparison
        for pic in broken_pics:
            # Skip the most-recent picture, it doesn't need its next_pic_ref fixed
            if pic.key == most_recent_key:
                continue

            next_pic = Picture.next_by_date(pic.date, or_equal_to=False)
            if next_pic is not None:
                pic.next_pic_ref = next_pic.key
                pic.put()
                _report_entry(pic, next_pic, 'next')

        # Fix broken prev links
        broken_pics = Picture.query(Picture.prev_pic_ref == None).iter() # pylint: disable=singleton-comparison
        for pic in broken_pics:
            # Skip the least-recent picture, it doesn't need its prev_pic_ref fixed
            if pic.key == least_recent_key:
                continue

            prev_pic = Picture.prev_by_date(pic.date, or_equal_to=False)
            if prev_pic is not None:
                pic.prev_pic_ref = prev_pic.key
                pic.put()
                _report_entry(pic, prev_pic, 'prev')

    message = "fix-next-prev"
    return render_template('admin_report.html', fixes=fixes, message=message)

@app.route('/smoke-test')
def smoke_test():
    """
    Smoke test for the
        next/prev links
        picture count
    """
    if not is_admin():
        abort(404, "smoke-test is admin-only")

    storage_client = storage.Client()
    blob_names = set([b.name for b in storage_client.list_blobs(GCS_BUCKET_NAME)])

    raw_counts = _counts()

    with client.context():
        picture = Picture.most_recent()
        if picture is None:
            pictures = []
            dates_sorted = []
            message = "no pictures"
        else:
            pictures = [picture]
            while picture.prev_pic_ref is not None:
                blob_names.discard(picture.name)
                tmp = picture
                picture = tmp.prev_pic
                pictures.append(picture)
            blob_names.discard(picture.name)
            dates = [str(p.date) for p in pictures]
            dates_sorted = sorted(dates, reverse=True)

            date_status = "correct" if dates == dates_sorted else "incorrect"

            pics_count_match = raw_counts['pics'] == len(pictures)
            blobs_count_match = raw_counts['blobs'] == len(pictures)
            count_match = pics_count_match and blobs_count_match
            count_status= "correct " if count_match else "incorrect"

            message = f"date ordering {date_status}, counts match {count_status} ({len(pictures)})"

        message = f"{message}, Counts: {raw_counts}, orphan blobs: {blob_names}"

        return render_template('admin_report.html', pictures=pictures,
            dates_sorted=dates_sorted, message=message, counts=raw_counts, zip=zip)

@app.route('/buckets')
def list_buckets():
    """List all buckets for this project."""
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()

    names = []
    for bucket in buckets:
        names.append(bucket.name)
    return ", ".join(names)

@app.route('/buckets/list')
def list_bucket():
    """List the contents of each GCS bucket for this project."""
    items = dict()
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()
    for bucket in buckets:
        if bucket.name not in items:
            items[bucket.name] = []
        for item in storage_client.list_blobs(GCS_BUCKET_NAME):
            items[bucket.name].append(item.name)

    return pprint.pformat(items)
