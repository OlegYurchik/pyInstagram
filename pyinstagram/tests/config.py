import json
import os


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")) as f:
    config = json.load(f)

accounts = config["accounts"]
creds = config["credentials"]
locations = config["locations"]
photos = config["photos"]
photo_sets = config["photo_sets"]
tags = config["tags"]
videos = config["videos"]
anon = config["anon"]
auth = config["auth"]
