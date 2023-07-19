"""
Apply a tag to all pictures between two added_order indices, inclusively
"""

import requests

FORWARD = True
DIRECTION = "next_added_order" if FORWARD else "prev_added_order"
METADATA_URL = "https://www.surlyfritter.com/p/meta/"
TAG_URL = "https://www.surlyfritter.com/tag/add"


def indices_set(start_index, end_index):
    """
    Navigate the next-image links from meta.next_added_order to get the list of
    images between start_index and end_index
    """
    indices = set([end_index])
    index = start_index
    while index not in indices:
        indices.add(index)
        resp = requests.get(f"{METADATA_URL}/{index}", timeout=15)
        index = resp.json()[DIRECTION]

    indices.add(index)
    return indices


places = {
    "paris": [7311, 7334],
    "brussells": [7281, 7274],
    "germany": [7364, 7386],
}

# For each place, start at the picture for the first index and generate a set
# of the images indices in date order between the start index and the stop
# index:
#
place_indices = {name: indices_set(*indices) for name, indices in places.items()}

# Apply the name tag to each index:
#
for name, indices in place_indices.items():
    for index in indices:
        data = dict(img_id=index, tag_text=name)
        requests.post(url=TAG_URL, data=data, timeout=15)
