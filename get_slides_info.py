#!/usr/bin/env python3

from hashlib import sha1
from time import time
from json import dumps
from getpass import getpass

import requests
from defusedxml.ElementTree import fromstring

api_key = "7LEe4yzP"
shared_secret = getpass("Enter Slideshare shared secret: ")
slideshare_user = "devday-dd"

ts = str(int(time()))

api_hash = sha1("".join((shared_secret, ts)).encode("utf8")).hexdigest()

r = requests.get(
    "https://www.slideshare.net/api/2/get_slideshows_by_user",
    params={
        "api_key": api_key,
        "hash": api_hash,
        "ts": ts,
        "username_for": slideshare_user
    })

data = fromstring(r.text)

slideshows = {}

for slideshow in data.iter('Slideshow'):
    embedkey = slideshow.find('SecretKey').text
    slideshows[embedkey] = {
        'id': slideshow.find('ID').text,
        'title': slideshow.find('Title').text,
        'url': slideshow.find('URL').text
    }

print(dumps(slideshows, sort_keys=True, indent=2))
