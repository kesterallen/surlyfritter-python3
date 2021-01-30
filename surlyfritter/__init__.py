
from flask import Flask
from google.cloud import ndb#, storage#, TODO vision
from surlyfritter.models import GCS_BUCKET_NAME_PREFIX

app = Flask(__name__)
app.secret_key = 'any random string'
client = ndb.Client(project=GCS_BUCKET_NAME_PREFIX)

import surlyfritter.routes
import surlyfritter.admin_routes
import surlyfritter.static_routes
import surlyfritter.quarantime
import surlyfritter.recipes

