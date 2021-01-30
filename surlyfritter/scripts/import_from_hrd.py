
import re
import requests
import random
import time

def get_meta(img_id):
    hrd_url = f"http://www.surlyfritter.com/meta/{img_id}"
    res = requests.get(hrd_url)
    json = res.json()

    date_parts = re.split(r'\s+', json['picture_index_date_order_string'])
    date = " ".join(date_parts[:2])
    date_order = date_parts[-1]

    meta = dict(
        added_order=json['picture_index_count'],
        date_order=date_order,
        date=date,
        url=json['url'],
        tags=json['tags'],
        comments=json['comments'],
    )
    return meta


upload_url = "http://localhost:8080/import/hrd"
img_ids = range(5219, 6521 + 1)

#TODO: there is at least one gap (permID = 2600), also 5218

# IDs must be in old site's added order order
# IDs must be in old site's added order order
# IDs must be in old site's added order order

failures = []
for img_id in img_ids:
    # get metadata
    try:
        meta = get_meta(img_id)
    except KeyError as err:
        failures.append(img_id)

    # submit the metadata to /import/hrd
    res = requests.post(upload_url, json=meta)
    print(img_id, res, meta)
    time.sleep(1)

print(failures)
