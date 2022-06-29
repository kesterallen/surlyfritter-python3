"""
Admin routes
"""

import datetime
import dateutil.parser
import io
import pprint
import requests

import jwt
from flask import redirect, request, abort, session

from google.cloud import storage
from google.cloud.exceptions import NotFound
#from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

from surlyfritter.models import Picture, Tag, Comment, GCS_BUCKET_NAME
from surlyfritter.utils import (
    send_email,
    render_template,
    #get_key,
    get_hash_from_url,
    is_logged_in,
    is_admin,
    get_exif_date_from_url,
)

from surlyfritter.fixtures.correct_ordering import (
    correct_picture_ordering,
    old_site_date_orders,
)

from . import app, client

DISABLE_DAMAGING_ENDPOINTS = True

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
    """Clear session of user info to log out"""
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
    #client_id = get_key('onetap_key')
    #decoded_token = jwt.decode(csrf_token_body, options={"verify_signature": False}) # pylint: disable=line-too-long

    #idinfo = id_token.verify_oauth2_token(decoded_token, g_requests.Request(), client_id) # pylint: disable=line-too-long

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
@app.route('/picture/nullrefs/<int:img_id>', methods=['POST'])
def picture_null_refs(img_id:int):
    """
    Null the next / previous links for this picture. Used for date linkage
    cleanup.
    """

    # ABORT
    if DISABLE_DAMAGING_ENDPOINTS:
        abort(404, "delete-all is a disabled endpoint")

    if not is_admin():
        abort(404, "null is admin-only")

    with client.context():
        picture = Picture.query(Picture.added_order == img_id).get()
        if picture is None:
            abort(404, f"Cannot find picture with added_order = {img_id}")
        picture.prev_pic_ref = None
        picture.next_pic_ref = None
        picture.put()

# TODO: remove this
@app.route('/delete/all')
def delete_everything():
    """Erase everything"""
    # TODO: ask if user is sure before doing this

    # ABORT
    if DISABLE_DAMAGING_ENDPOINTS:
        abort(404, "delete-all is a disabled endpoint")

    if not is_admin():
        abort(404, "delete-all is admin-only")

    deletes = dict(
        blobs=[],
        pictures=[],
        tags=[],
        comments=[],
    )
    with client.context():
        for picture in Picture.query().iter():

            try:
                # Delete blob with picture.name
                storage_client = storage.Client()
                bucket = storage_client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(picture.name)
                blob.delete()
                deletes['blobs'].append(picture.name)
            except:
                deletes['blobs'].append(f"failure: {picture.name}")

            try:
                # Delete picture
                picture.key.delete()
                deletes['pictures'].append(picture.name)
            except:
                deletes['pictures'].append(f"failure: {picture.name}")

        for tag in Tag.query().iter():
            tag.key.delete()
            deletes['tags'].append(tag.text)

        for comment in Comment.query().iter():
            comment.key.delete()
            deletes['comments'].append(comment.text)

    message = "Delete report:"
    return render_template('admin_report.html', deletes=deletes, message=message)

def _picture_edit_post(img_id:int):
    """POST: Make the picture edit changes"""
    # TODO remove/edit comment or tag

    try:
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

        # Alter .date:
        new_date = request.form.get("new_date")
        if new_date:
            date = dateutil.parser.parse(new_date)
            picture.date = date

            # set prev_pic's .next_pic_ref to next_pic, if prev_pic exists (or None, if next_pic doesn't exist)
            if picture.next_pic_ref:
                picture.prev_pic.next_pic_ref = picture.next_pic.key

            # set next_pic's .prev_pic_ref to prev_pic, if next_pic exists (or None, if prev_pic doesn't exist)
            if picture.prev_pic_ref:
                picture.next_pic.prev_pic_ref = picture.prev_pic.key

            # set new next_pic and prev_pic to point to picture, and
            # picture.next_pic_ref and picture.prev_pic_ref to point to
            # new next/prev
            prev_pic_key, next_pic_key = Picture.prev_next_pic_keys(date)
            picture.prev_pic_ref = prev_pic_key
            #TODO: need to picture.put() first?
            picture.prev_pic.next_pic_ref = picture.key
            picture.next_pic_ref = next_pic_key
            #TODO: need to picture.put() first?
            picture.next_pic.prev_pic_ref = picture.key

        picture.updated_on = datetime.datetime.now()
        picture.put()
    except NotFound as err: # blob not found
        abort(404, f"Blob with {picture.name} not found, exiting ({err})")

    return redirect(f"/p/{picture.imgp_id}")

def _picture_edit_get(img_id:int):
    """GET: Render form with optional message"""
    picture = Picture.query(Picture.added_order == img_id).get()

    exif_date = get_exif_date_from_url(picture.img_url)

    if picture is None:
        abort(404, f"Cannot find picture with added_order = {img_id}")
    message = "Edit Mode"

    return render_template('add.html', message=message,
        edit_picture=picture, exif_date=exif_date)

@app.route('/picture/edit/<int:img_id>', methods=['GET', 'POST'])
def picture_edit(img_id:int):
    """Edit a Picture that already exists"""

    if not is_admin():
        abort(404, "edit is admin-only")

    with client.context():
        if request.method == 'POST':
            return _picture_edit_post(img_id)
        return _picture_edit_get(img_id)

@app.route('/picture/delete/<int:img_id>')
def picture_delete(img_id:int):
    """Delete a Picture and its blob (by the .added_order attribute)"""
    if not is_admin():
        abort(404, "picture delete is admin-only")

    with client.context():
        try:
            picture = Picture.query(Picture.added_order == img_id).get()
            if picture is None:
                abort(404, f"Cannot find picture with added_order = {img_id}")
            metadata = picture.json

            # delete blob with picture.name
            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(picture.name)
            blob.delete()
        except NotFound as err: # blob not found
            #abort(404, f"Blob with {picture.name} not found, exiting")
            print(f"no blob for .added_order {img_id}: {err}")

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
        return f"deleted {img_id}:\n{metadata}"

@app.route('/import/hrd', methods=['POST'])
def import_hrd():
    """
    Import data from an HRD image's metadata JSON

    TODO: HRD import must be done in old site's added_order order to preserve
    added_order
    """

    # ABORT
    if DISABLE_DAMAGING_ENDPOINTS:
        abort(404, 'Import-HRD is disabled')

    hrd_meta = request.get_json(force=True)

    # Download image from old site:
    try:
        response = requests.get(hrd_meta['url']) # N.B. 'requestS' library
        img = io.BytesIO(response.content)
        now = datetime.datetime.now().timestamp()
        added_order = hrd_meta['added_order']
        name = f"hrd_import_{added_order}_{now}.jpg"
        date = datetime.datetime.strptime(hrd_meta['date'], '%Y:%m:%d %H:%M:%S')

        picture = Picture.create(img, name, date)

        # Add comments and tags:
        with client.context():
            for tag in hrd_meta['tags']:
                picture.add_tag(tag)
            for comment in hrd_meta['comments']:
                picture.add_comment(comment)
    except:
        abort(404, f'Import-HRD failure for {hrd_meta["url"]}')

    return hrd_meta

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
    DO_HASH_CHECK = False

    if not is_admin():
        abort(404, "smoke-test is admin-only")

    storage_client = storage.Client()
    blob_names = {b.name for b in storage_client.list_blobs(GCS_BUCKET_NAME)}

    raw_counts = _counts()

    if DO_HASH_CHECK:
        ihash = 0
        image_hashes = dict()

    i = 1
    with client.context():
        picture = Picture.most_recent()

        # If not pictures, bail:
        if picture is None:
            return render_template('admin_report.html', pictures=[],
                correct_ordering=[], message="no pictures", counts=raw_counts, zip=zip)

        # If there are pictures, check them:

        # Walk backwards through the pictures from most recent to earliest
        # using the previous pic references:
        pictures = [picture]
        visited_pics = {picture.imgp_id: None}
        while picture.prev_pic_ref is not None:
            blob_names.discard(picture.name)
            tmp = picture
            picture = tmp.prev_pic
            print("smoke-test status:", i, tmp.imgp_id, picture.imgp_id)
            i += 1
            pictures.append(picture)

            if picture.imgp_id in visited_pics:
                msg = (
                    f"Abort: circular path: picture {picture.imgp_id} has"
                    f" already been visited by {visited_pics[picture.imgp_id]}"
                    f" and is not being visited by {tmp.imgp_id}"
                    f" ({len(visited_pics)} pics visited)")
                abort(400, msg)
            visited_pics[picture.imgp_id] = tmp.imgp_id

            if DO_HASH_CHECK:
                # Check for duplicate images. SLOW
                hash_value = get_hash_from_url(picture.img_url)
                ihash += 1
                print(f"doing {ihash} hash for {picture.imgp_id}")
                if hash_value not in image_hashes:
                    # New hash -- not a duplicate image
                    image_hashes[hash_value] = [picture.imgp_id]
                else:
                    # Duplicate image, append the new image ID:
                    image_hashes[hash_value].append(picture.imgp_id)

        # Discard the final picture's blob name so it isn't marked as an
        # orphan:
        blob_names.discard(picture.name)

        # Check the dates sorting is correct:
        dates_imgp = [p.imgp_id for p in pictures]
        date_status = "correct" if dates_imgp[-len(correct_picture_ordering):] == correct_picture_ordering else "incorrect"

        # Check the counts are correct
        pics_count_match = raw_counts['pics'] == len(pictures)
        blobs_count_match = raw_counts['blobs'] == len(pictures)
        count_match = pics_count_match and blobs_count_match
        count_status= "correct " if count_match else "incorrect"

        message = f"date ordering {date_status} / counts match {count_status}"

        if DO_HASH_CHECK:
            # Flag any duplicate images:
            duplicate_images = []
            for hash_value, imgp_ids in image_hashes.items():
                if len(imgp_ids) > 1:
                    duplicate_images.append(imgp_ids)
            message = f"{message}, duplicate images: {duplicate_images}"

        orphan_message = f"orphan blobs: {blob_names}" if blob_names else "no orphans"
        message = f"{message}, {orphan_message}"

        return render_template('admin_report.html', pictures=pictures,
            correct_ordering=correct_picture_ordering, message=message, counts=raw_counts, zip=zip)

@app.route('/buckets')
def list_buckets():
    """List all buckets for this project."""
    storage_client = storage.Client()
    buckets = storage_client.list_buckets()
    names = [b.name for b in buckets]
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

@app.route('/fixtures')
def fixtures():
    return(", ".join([str(x) for x in correct_picture_ordering])
        + ", ".join([str(x) for x in old_site_date_orders]))

@app.route('/reverttooldsitedateorder')
def revert_to_old_site_date_order():
    # from https://surlyfritter-hrd.appspot.com/listdate
    # fold the next 6500 lines in vim for better editing
    if not is_admin():
        abort(404, "reverttooldsitedateorder is admin-only")

    with client.context():
        def _get_prev_picture(i):
            i_prev = i + 1
            prev_picture = None
            while prev_picture is None:
                added_order = old_site_date_orders[i_prev][1]
                prev_picture = Picture.query(Picture.added_order == added_order).get()
                i_prev += 1
            return prev_picture

        def _get_next_picture(i):
            i_next = i - 1
            next_picture = None
            while next_picture is None:
                added_order = old_site_date_orders[i_next][1]
                next_picture = Picture.query(Picture.added_order == added_order).get()
                i_next -= 1
            return next_picture

        for i in range(len(old_site_date_orders)):
            date_order, added_order = old_site_date_orders[i]
            print(f"{i} -- date order: {date_order}, added order: {added_order}")

            picture = Picture.query(Picture.added_order == added_order).get()
            if picture is None:
                print(f"Skipping {i} -- no picture")
                continue

            if i == 0:
                print("special most-recent picture logic")
                prev_picture = _get_prev_picture(i)
                prev_picture.next_pic_ref = picture.key
                picture.prev_pic_ref = prev_picture.key

                picture.next_pic_ref = None
                # TODO: run fix_6521():

                picture.put()
                prev_picture.put()
            elif i == (len(old_site_date_orders)-1):
                print("special earliest picture logic")
                next_picture = _get_next_picture(i)
                next_picture.prev_pic_ref = picture.key
                picture.next_pic_ref = next_picture.key

                picture.prev_pic_ref = None

                picture.put()
                next_picture.put()
            else:
                #print("regular case")
                prev_picture = _get_prev_picture(i)
                prev_picture.next_pic_ref = picture.key
                picture.prev_pic_ref = prev_picture.key

                next_picture = _get_next_picture(i)
                next_picture.prev_pic_ref = picture.key
                picture.next_pic_ref = next_picture.key

                picture.put()
                prev_picture.put()
                next_picture.put()

    return "done"

@app.route('/fix6521')
def fix_6521():
    if not is_admin():
        abort(404, "fix_6521 is admin-only")
    with client.context():
        picture = Picture.query(Picture.added_order == 6521).get()
        next_picture = Picture.query(Picture.added_order == 6522).get()

        next_picture.prev_pic_ref = picture.key
        picture.next_pic_ref = next_picture.key

        picture.put()
        next_picture.put()
