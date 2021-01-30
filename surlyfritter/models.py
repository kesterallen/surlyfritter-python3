"""
Model classes for picture site
"""

#TODO print --> logging

import datetime
from google.cloud import ndb, storage
import math

DOB = dict(
    miri=datetime.datetime(2007, 10, 26, 5, 30, 0),
    julia=datetime.datetime(2010, 4, 21, 7, 30, 0),
    linus=datetime.datetime(2015, 4, 18, 5, 30, 0),
)

DAYS_IN_YEAR = 365.25
SECS_IN_YEAR = DAYS_IN_YEAR * 3600 * 24

GCS_BUCKET_NAME_PREFIX = "surlyfritter-python3"
GCS_BUCKET_NAME = f"{GCS_BUCKET_NAME_PREFIX}.appspot.com"

client = ndb.Client(project=GCS_BUCKET_NAME_PREFIX)

class Comment(ndb.Model):
    """Freeform comments about a picture."""
    text = ndb.StringProperty()
    added_on = ndb.DateTimeProperty(auto_now_add=True)

class Tag(ndb.Model):
    """Freeform tag about a picture."""
    text = ndb.StringProperty()
    tag_count = ndb.IntegerProperty()
    tag_count_log = ndb.FloatProperty() # precompute this, useful for font sizing in tag cloud
    added_on = ndb.DateTimeProperty(auto_now_add=True)

class Picture(ndb.Model):
    """The main object."""
    name = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    added_on = ndb.DateTimeProperty(auto_now_add=True)
    updated_on = ndb.DateTimeProperty(auto_now_add=True)
    added_order = ndb.IntegerProperty()

    prev_pic_ref = ndb.KeyProperty(kind='Picture')
    next_pic_ref = ndb.KeyProperty(kind='Picture')

    tag_refs = ndb.KeyProperty(kind='Tag', repeated=True)
    comment_refs = ndb.KeyProperty(kind='Comment', repeated=True)

    img_rot = ndb.IntegerProperty()

    @classmethod
    def blob_create(cls, img, name):
        """ Create or overwrite a blob image. """
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(name)
        blob.upload_from_file(img, content_type="image/jpeg")

    @classmethod
    def create(cls, img, name, date):
        """
        Set this picture's prev and next pointers to the right entities, and
        update the previous's pic.next and the next's pic.prev to point to the
        current (new) picture:
        """
        with client.context():
            prev_pic = Picture.prev_by_date(date)
            prev_pic_key = None if prev_pic is None else prev_pic.key

            next_pic = Picture.next_by_date(date)
            next_pic_key = None if next_pic is None else next_pic.key

            picture = Picture(
                name=name,
                date=date,
                added_on=datetime.datetime.now(),
                added_order=Picture.next_added_order(),
                prev_pic_ref=prev_pic_key,
                next_pic_ref=next_pic_key,
            )
            picture.put()

            if prev_pic is not None:
                prev_pic.next_pic_ref = picture.key
                prev_pic.put()
            if next_pic is not None:
                next_pic.prev_pic_ref = picture.key
                next_pic.put()

            # Make blob from file:
            Picture.blob_create(img, name)

        return picture

    @classmethod
    def next_by_date(cls, date, or_equal_to=False):
        """
        Get the Picture that is next after 'date' if there are more than one,
        return the entity with the lowest added_order. Return None if there are no
        entites with .date > 'date'

        Default for '>', override this if you want to not return an identical
        Picture item.
        """
        if or_equal_to:
            query = Picture.query(Picture.date >= date)
        else:
            query = Picture.query(Picture.date > date)

        picture = query.order(Picture.date, Picture.added_order).get()
        return picture

    @classmethod
    def prev_by_date(cls, date, or_equal_to=True):
        """
        Get the Picture that is previous to 'date', if there are more than one,
        return the entity with the highest added_order. Return None if there
        are no entites with .date <= 'date'

        Default for '<=', override this for /fix-next-prev if you want too not
        return an identical Picture item.
        """
        if or_equal_to:
            query = Picture.query(Picture.date <= date)
        else:
            query = Picture.query(Picture.date < date)

        picture = query.order(-Picture.date, -Picture.added_order).get()
        return picture

    @classmethod
    def with_tag(cls, tag_text, num=None):
        """
        Get 'num' (or all if num is None) pictures with who contain a tag with
        .text of 'tag_text'.
        """
        tag = Tag.query(Tag.text == tag_text).get()
        if tag:
            query = Picture.query(Picture.tag_refs == tag.key
                ).order(-Picture.added_order)
            pictures = query.fetch() if num is None else query.fetch(num)
        else:
            pictures = None
        return pictures

    @classmethod
    def _timejump(cls, now_date, years) -> datetime:
        """Return the datetime object for years + now_date"""
        timedelta = datetime.timedelta(days=DAYS_IN_YEAR*years)
        new_date = now_date + timedelta
        return new_date

    @classmethod
    def timejump_index(cls, added_order, years) -> int:
        """
        Return the .added_order attribute of the Picture closest to
        'years' + the date of the Picture with .added_order= 'added_order'
        """
        picture = Picture.query(Picture.added_order == added_order).get()
        timedelta = datetime.timedelta(days=DAYS_IN_YEAR*years)
        to_date = picture.date + timedelta
        dest_picture = Picture.from_date(to_date)
        return dest_picture.imgp_id

    @classmethod
    def kid_is_index(cls, name, age) -> int:
        """
        Return the .added_order for the Picture from 'name' at 'age' years old.
        """
        years = float(age)
        now_date = DOB.get(name, 'miri')
        to_date = Picture._timejump(now_date, years)
        dest_picture = Picture.from_date(to_date)
        return dest_picture.imgp_id

    @classmethod
    def from_date(cls, date:datetime) -> int:
        """
        Get the added_order of the Picture that is closest to 'date'
        """
        picture = Picture.next_by_date(date)
        if picture is None:
            # If date is outside the range of dates there are Picture for, get
            # either the closet previous or closest after picture:
            picture = Picture.prev_by_date(date)
            if picture is None:
                picture = Picture.next_by_date(date)

        return picture

    @classmethod
    def next_added_order(cls):
        """ Return the most recently added Picture's .added_order"""
        picture = Picture.query().order(-Picture.added_order).get()
        added_order = 0 if picture is None else picture.added_order + 1
        return added_order

    @classmethod
    def last_added(cls):
        """ Return the most recently added Picture, by .added_order """
        picture = Picture.query().order(-Picture.added_order).get()
        return picture

    @classmethod
    def most_recent(cls):
        """ Return the most recent Picture, by .date"""
        picture = Picture.query().order(-Picture.date).get()
        return picture

    @classmethod
    def first_added(cls):
        """ Return the first-added Picture, by .added_order """
        picture = Picture.query().order(Picture.added_order).get()
        return picture

    @classmethod
    def least_recent(cls):
        """ Return the most recent Picture, by .date"""
        picture = Picture.query().order(Picture.date).get()
        return picture

    @property
    def date_display(self):
        utc_offset = datetime.timedelta(hours=8)
        return (self.date - utc_offset).strftime('%B %-d, %Y (%-I:%M %p)')

    @property
    def tags(self):
        """The tags associated with this entity, as a list"""
        return [t.get() for t in self.tag_refs]

    @property
    def tags_str(self):
        """The tags associated with this entity, as a joined string"""
        return ", ".join([t.text for t in self.tags])

    @property
    def comments(self):
        """The comments associated with this entity, as a list"""
        return [c.get() for c in self.comment_refs]

    @property
    def comments_str(self):
        """The comments associated with this entity, as a joined string"""
        return ", ".join([c.text for c in self.comments])

    @property
    def prev_pic(self):
        """The picture pointed to by the prev_pic_ref for this entity"""
        return self.prev_pic_ref.get()

    @property
    def next_pic(self):
        """The picture pointed to by the next_pic_ref for this entity"""
        return self.next_pic_ref.get()

    @property
    def imgp_id(self) -> int:
        """Alias for added_order"""
        return self.added_order

    @property
    def img_url(self) -> str:
        """
        Return the URL for the image for this object. The image is a blob in
        the modern GCS storage.
        """
        url_prefix = "https://storage.googleapis.com"
        url = f"{url_prefix}/{GCS_BUCKET_NAME}/{self.name}"
        return url

    @property
    def meta(self) -> str:
        """Picture metadata, returned as JSON by flask"""
        meta_str = dict(
            name=self.name,
            date=self.date,
            key=str(self.key),
            added_order=self.added_order,
            prev_ref=str(self.prev_pic_ref),
            next_ref=str(self.next_pic_ref),
            tags=[t.text for t in self.tags],
            comments=[c.text for c in self.comments],
            url=self.img_url,
        )
        return meta_str

    @property
    def json(self):
        return dict(added_order=self.added_order, key=str(self.key), date=self.date)

    def add_tag(self, tag_text:str):
        """Add a tag to this Picture, avoiding duplicates"""
        # TODO this incorrectly increases the tag_count and tag_count_log if the tag is a duplicate for this pictures
        tag = Tag.query(Tag.text == tag_text).get()

        # Check if this Tag is already associated with this Picture (duplicate
        # entry in the form?). If it is, return. If there isn't a Tag with this
        # .text yet, create one and associate it with the Picture:
        #
        if tag is not None:
            if tag.key in self.tag_refs:
                return
        else:
            tag = Tag(text=tag_text, tag_count=0)

        tag.tag_count += 1
        tag.tag_count_log = math.log10(tag.tag_count)
        tag.put()

        self.tag_refs.append(tag.key)
        self.put()

    def add_comment(self, comment_text:str):
        """Add a comment to this Picture"""
        comment = Comment(text=comment_text)
        comment.put()
        self.comment_refs.append(comment.key)
        self.put()
