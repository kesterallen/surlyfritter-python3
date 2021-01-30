"""
Main run script
"""
from surlyfritter import app

#SET THIS envar TO GET CREDS:
#
#GOOGLE_APPLICATION_CREDENTIALS=/home/kester/Desktop/gae_tutorial/python-docs-samples/appengine/standard_python3/surlyfritter-python3-2ce73610c763.json
# [START gae_python38_app]

# TODO:
# Email pictures
# Nice response for pictures that don't exist.
#    * redirect back to previous?
#    * bracket to highest/lowest?
#    * /\d*.jpg
#    * /exiv/\d+
# TODO: rotate images as required?

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python38_app]
