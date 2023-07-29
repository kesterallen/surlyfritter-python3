"""Script to upload groups of images to surlyfritter.com."""

import datetime
import sys
import time
import requests

DEBUG = False
ONLY_DO_THIS_MANY_UPLOADS = 0


class SurlyfritterImage:
    """
    Class to encapsulate the image/location of the image, and provide a method
    to submit the object to surlyfritter.
    """

    URL = "https://www.surlyfritter.com/picture/add"

    def __init__(self, fname):
        """Simple constructor."""
        self.fname = fname

    def submit(self):
        """Submit the SurlyfritterImage with a POST request to surlyfritter"""

        with open(self.fname, "rb") as image_fh:
            files = {"pictures": image_fh}
            data = {}
            response = requests.post(SurlyfritterImage.URL, files=files, data=data, timeout=60)
            response.raise_for_status()

    def __repr__(self):
        return self.fname


def main(img_fnames):
    """
    For a given list of images, make SurlyfritterImage instances and submit
    them to surlyfritter.
    """
    tfirst = datetime.datetime.now()
    images = []
    print(f"Loading {len(img_fnames)} images")
    for fname in img_fnames:
        image = SurlyfritterImage(fname)
        images.append(image)
    print("Loading complete")

    successes = []
    failures = []

    for i, image in enumerate(images):
        msg = f"{i+1} / {len(images)} {image}"
        if i < ONLY_DO_THIS_MANY_UPLOADS:  # tweak this for debugging
            print("skipping", msg)
            continue
        print(f"posting {msg}", end="")

        try:
            tstart = datetime.datetime.now()
            image.submit()
            tend = datetime.datetime.now()
            print(" ", tend - tstart)
            successes.append(image.fname)
        except requests.exceptions.HTTPError:
            failures.append(image.fname)
            print(", failed")
        if not DEBUG:
            time.sleep(60)

    msgs = []
    if successes:
        msgs.extend(["\nUploaded successfully:"] + successes)
    if failures:
        msgs.extend(["\n\nFailed:"] + failures)
    print("\n\t".join(msgs))
    print(datetime.datetime.now() - tfirst, " total time")


if __name__ == "__main__":
    main(sys.argv[1:])
