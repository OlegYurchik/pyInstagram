import pytest
from random import randint

from instaparser.agents import Agent
from instaparser.entities import Account, Media, Location, Tag



account_username = "zuck"
photo_shortcode = "BTcb3esjjVo"
photo_set_shortcode = "BZF0fbXj3zV"
video_shortcode = "BV76rluDGsC"
location_id = 251729389
tag_name = "instagram"



def test_update():
    anon = Agent()
    
    anon.update()
    
    assert(not getattr(anon, "_rhx_gis", None) is None)
    assert(not getattr(anon, "_csrf_token", None) is None)


def test_update_account():
    anon = Agent()
    account = Account(account_username)
    
    data = anon.update(account)
    
    assert(not data is None)
    
    Account.clear_cache()


def test_update_photo():
    anon = Agent()
    photo = Media(photo_shortcode)

    data = anon.update(photo)

    assert(not photo.is_video)

    Media.clear_cache()


def test_update_photo_set():
    anon = Agent()
    photo_set = Media(photo_set_shortcode)
    
    data = anon.update(photo_set)
    
    assert(not photo_set.is_video)
    
    Media.clear_cache()


def test_update_video():
    anon = Agent()
    video = Media(video_shortcode)
    
    data = anon.update(video)
    
    assert(video.is_video)
    
    Media.clear_cache()


def test_update_location():
    anon = Agent()
    location = Location(location_id)
    
    data = anon.update(location)
    
    Location.clear_cache()


def test_update_tag():
    anon = Agent()
    tag = Tag(tag_name)
    
    data = anon.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("count", [randint(100, 500) for i in range(3)])
def test_get_media_account(count):
    anon = Agent()
    account = Account(account_username)
    
    data, pointer = anon.get_media(account, count=count)

    assert(min(account.media_count, count) >= len(data))
    assert((pointer is None) == (account.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(100, 500) for i in range(3)])
def test_get_media_location(count):
    anon = Agent()
    location = Location(location_id)
    
    data, pointer = anon.get_media(location, count=count)

    assert(min(location.media_count, count) >= len(data))
    assert((pointer is None) == (location.media_count <= count))

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(100, 500) for i in range(3)])
def test_get_media_tag(count):
    anon = Agent()
    tag = Tag(tag_name)
    
    data, pointer = anon.get_media(tag, count=count)

    assert(min(tag.media_count, count) >= len(data))
    assert((pointer is None) == (tag.media_count <= count))

    Tag.clear_cache()
    Media.clear_cache()


def test_get_likes():
    anon = Agent()
    photo = Media(photo_shortcode)
    
    data, pointer = anon.get_likes(photo)
    
    assert(photo.likes_count >= len(data))

    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(100, 500) for i in range(3)])
def test_get_comments(count):
    anon = Agent()
    media = Media(photo_shortcode)
    
    data, pointer = anon.get_comments(media, count=count)
    
    assert(min(media.comments_count, count) >= len(data))
    assert((pointer is None) == (media.likes_count <= count))

    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(5000, 10000)])
def test_get_media_account_long(count):
    anon = Agent()
    account = Account(account_username)
    
    anon.update(account)
    
    count = account.media_count
    
    data, pointer = anon.get_media(account, count=count)

    assert(min(account.media_count, count) >= len(data))
    assert((pointer is None) == (account.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(5000, 10000)])
def test_get_media_location_long(count):
    anon = Agent()
    location = Location(location_id)
    
    data, pointer = anon.get_media(location, count=count)

    assert(min(location.media_count, count) >= len(data))
    assert((pointer is None) == (location.media_count <= count))

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(5000, 10000)])
def test_get_media_tag_long(count):
    anon = Agent()
    tag = Tag(tag_name)
    
    data, pointer = anon.get_media(tag, count=count)

    assert(min(tag.media_count, count) >= len(data))
    assert((pointer is None) == (tag.media_count <= count))

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("count", [randint(5000, 10000)])
def test_get_comments_long(count):
    anon = Agent()
    media = Media(photo_shortcode)
    
    data, pointer = anon.get_comments(media, count=count)
    
    assert(min(media.comments_count, count) >= len(data))
    assert((pointer is None) == (media.likes_count <= count))

    Media.clear_cache()
