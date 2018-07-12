import pytest
from random import randint

from instaparser.agents import AgentAccount
from instaparser.entities import Account, Media, Location, Tag



login = "oleg.yurchik"
password = "Cola1995"
account_username = "zuck"
photo_shortcode = "BTcb3esjjVo"
photo_set_shortcode = "BZF0fbXj3zV"
video_shortcode = "BV76rluDGsC"
location_id = 251729389
tag_name = "instagram"


def auth():
    agent = AgentAccount(login, password)
    
    Account.clear_cache()


def 
