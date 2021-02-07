"""Surlyfritter picture site"""

from flask import Flask
from google.cloud import ndb
from surlyfritter.models import GCS_BUCKET_NAME_PREFIX

app = Flask(__name__)
app.secret_key = 'any random string'
client = ndb.Client(project=GCS_BUCKET_NAME_PREFIX)

import surlyfritter.routes # pylint: disable=cyclic-import disable=wrong-import-position
import surlyfritter.admin_routes # pylint: disable=cyclic-import disable=wrong-import-position
import surlyfritter.static_routes # pylint: disable=cyclic-import disable=wrong-import-position
import surlyfritter.quarantime # pylint: disable=cyclic-import disable=wrong-import-position
import surlyfritter.recipes # pylint: disable=cyclic-import disable=wrong-import-position
