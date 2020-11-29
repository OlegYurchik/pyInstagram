import random

import pytest

from .. import config


def test_update(web_agent_account):
    data = web_agent_account.update()

    assert data is not None
    assert web_agent_account.id is not None
    assert web_agent_account.full_name is not None
    assert web_agent_account.profile_pic_url is not None
    assert web_agent_account.profile_pic_url_hd is not None
    assert web_agent_account.biography is not None
    assert web_agent_account.follows_count is not None
    assert web_agent_account.followers_count is not None
    assert web_agent_account.media_count is not None
    assert web_agent_account.is_private is not None
    assert web_agent_account.is_verified is not None
    assert web_agent_account.country_block is not None


@pytest.mark.parametrize("username", config.accounts)
def test_update_account(web_agent_account, username):
    account = Account(username)
    data = web_agent_account.update(account)

    assert data is not None
    assert web_agent_account.id is not None
    assert web_agent_account.full_name is not None
    assert web_agent_account.profile_pic_url is not None
    assert web_agent_account.profile_pic_url_hd is not None
    assert web_agent_account.biography is not None
    assert web_agent_account.follows_count is not None
    assert web_agent_account.followers_count is not None
    assert web_agent_account.media_count is not None
    assert web_agent_account.is_private is not None
    assert web_agent_account.is_verified is not None
    assert web_agent_account.country_block is not None


@pytest.mark.parametrize("shortcode", [
    random.choice(config.photos + config.photo_sets + config.videos),
])
def test_update_media(web_agent_account, shortcode):
    media = Media(shortcode)
    data = web_agent_account.update(media)

    assert data is not None
    assert media.id is not None
    assert media.code is not None
    assert media.date is not None
    assert media.likes_count is not None
    assert media.comments_count is not None
    assert media.comments_disabled is not None
    assert media.is_video is not None
    assert media.display_url is not None
    assert media.resources is not None
    assert media.is_album is not None


@pytest.mark.parametrize("id", config.locations)
def test_update_location(web_agent_account, id):
    location = Location(id)
    data = web_agent_account.update(location)

    assert data is not None
    assert location.id is not None
    assert location.slug is not None
    assert location.name is not None
    assert location.has_public_page is not None
    assert location.coordinates is not None
    assert location.media_count is not None


@pytest.mark.parametrize("name", config.tags)
def test_update_tag(web_agent_account, name):
    tag = Tag(name)
    data = web_agent_account.update(tag)

    assert data is not None
    assert tag.name is not None
    assert tag.media_count is not None
    assert tag.top_posts


@pytest.mark.parametrize("count, username", [
    (random.randint(100, 500), random.choice(config.accounts)),
])
def test_get_media_account(web_agent_account, delay, count, username):
    account = Account(username)
    data, pointer = web_agent_account.get_media(account, count=count, delay=delay)

    assert min(account.media_count, count) == len(data)
    assert (pointer is None) == (account.media_count <= count)


@pytest.mark.parametrize("count, id",  [
    (random.randint(100, 500), random.choice(config.locations)),
])
def test_get_media_location(web_agent_account, delay, count, id):
    location = Location(id)
    data, pointer = web_agent_account.get_media(location, count=count, delay=delay)

    assert min(location.media_count, count) == len(data)
    assert (pointer is None) == (location.media_count <= count)


@pytest.mark.parametrize("count, name",  [(random.randint(100, 500), random.choice(config.tags))])
def test_get_media_tag(web_agent_account, delay, count, name):
    tag = Tag(name)
    data, pointer = web_agent_account.get_media(tag, count=count, delay=delay)

    assert min(tag.media_count, count) == len(data)
    assert (pointer is None) == (tag.media_count <= count)


@pytest.mark.parametrize("shortcode", [
    random.choice(config.photos),
    random.choice(config.photo_sets),
    random.choice(config.videos),
])
def test_get_likes(web_agent_account, shortcode):
    media = Media(shortcode)
    data, _ = web_agent_account.get_likes(media)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize(
    "count, shortcode",
    [(random.randint(100, 500), shortcode) for shortcode in [
        random.choice(config.photos),
        random.choice(config.photo_sets),
        random.choice(config.videos),
    ]],
)
def test_get_comments(web_agent_account, delay, count, shortcode):
    media = Media(shortcode)
    data, pointer = web_agent_account.get_comments(media, count=count, delay=delay)

    assert min(media.comments_count, count) == len(data)
    assert (pointer is None) == (media.comments_count <= count)


@pytest.mark.parametrize("count, username", [
    (random.randint(100, 500), random.choice(config.accounts)),
])
def test_get_follows(web_agent_account, delay, count, username):
    account = Account(username)
    data, pointer = web_agent_account.get_follows(account, count=count, delay=delay)

    assert min(account.follows_count, count) == len(data)
    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [
    (random.randint(100, 500), random.choice(config.accounts)),
])
def test_get_followers(web_agent_account, delay, count, username):
    account = Account(username)
    data, pointer = web_agent_account.get_followers(
        account,
        count=count,
        delay=delay,
    )

    assert min(account.followers_count, count) == len(data)
    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count", [random.randint(100, 500)])
def test_get_feed(web_agent_account, delay, count):
    data, pointer = web_agent_account.feed(count=count, delay=delay)

    assert (count > len(data)) == (pointer is None)


def test_get_stories(web_agent_account):
    web_agent_account.stories()


@pytest.mark.parametrize("count, username", [
    (random.randint(1, 10), random.choice(config.accounts)),
])
def test_get_media_account_pointer(web_agent_account, delay, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_media(account, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.media_count == len(data))


@pytest.mark.parametrize("count, id", [(random.randint(1, 10), random.choice(config.locations))])
def test_get_media_location_pointer(web_agent_account, delay, count, id):
    location = Location(id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_media(location, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (location.media_count == len(data))


@pytest.mark.parametrize("count, name", [(random.randint(1, 10), random.choice(config.tags))])
def test_get_media_tag_pointer(web_agent_account, delay, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_media(tag, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (tag.media_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [(random.randint(1, 10), shortcode) for shortcode in [
        random.choice(config.photos),
        random.choice(config.photo_sets),
        random.choice(config.videos),
    ]],
)
def test_get_comments_pointer(web_agent_account, delay, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_comments(media, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.comments_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [(random.randint(1, 10), random.choice(config.photos + config.photo_sets + config.videos))],
)
def test_get_likes_pointer(web_agent_account, delay, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_likes(media, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (media.likes_count <= count)


@pytest.mark.parametrize("count, username", [
    (random.randint(1, 10), random.choice(config.accounts)),
])
def test_get_follows_pointer(web_agent_account, delay, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_follows(account, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [
    (random.randint(1, 10), random.choice(config.accounts)),
])
def test_get_followers_pointer(web_agent_account, delay, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.get_followers(account, pointer=pointer)
        sleep(delay)
        data.extend(tmp)

    assert (pointer is None) == (account.followers_count <= count)


@pytest.mark.parametrize("count", [random.randint(1, 10)])
def test_get_feed_pointer(web_agent_account, delay, count):
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = web_agent_account.feed(pointer=pointer)
        sleep(delay)
        data.extend(tmp)


@pytest.mark.parametrize("shortcode", [
    random.choice(config.photos + config.photo_sets + config.videos),
])
def test_like_unlike_media(web_agent_account, delay, shortcode):
    photo = Media(shortcode)

    assert web_agent_account.like(photo)
    sleep(delay)
    assert web_agent_account.unlike(photo)


@pytest.mark.parametrize("username", [random.choice(config.accounts)])
def test_follow_unfollow(web_agent_account, delay, username):
    account = Account(username)
    web_agent_account.update()
    follows_count = web_agent_account.follows_count

    assert web_agent_account.follow(account)
    sleep(delay)
    web_agent_account.update()
    assert web_agent_account.follows_count == follows_count + 1
    assert web_agent_account.unfollow(account)
    sleep(delay)
    web_agent_account.update()
    assert web_agent_account.follows_count == follows_count


@pytest.mark.parametrize("shortcode", [
    random.choice(config.photos + config.photo_sets + config.videos),
])
def test_comment(web_agent_account, delay, shortcode):
    media = Media(shortcode)
    comment = web_agent_account.add_comment(media, "test")
    sleep(delay)

    assert web_agent_account.delete_comment(comment)
