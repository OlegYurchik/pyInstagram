import pytest
from random import randint, choice

from instaparser.agents import AgentAccount
from instaparser.entities import Account, Media, Location, Tag, Comment

from tests.settings import accounts, creds, locations, photos, photo_sets, tags, videos



def parametrize(*args):
    result = []
    for variable in zip(*args):
        result.append((creds["login"], creds["password"], *variable))
    return result



@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_auth(login, password):
    agent = AgentAccount(login, password)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_update(login, password):
    agent = AgentAccount(login, password)
    
    agent.update()
    
    assert(not getattr(agent, "id") is None)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,username", parametrize(accounts))
def test_update_account(login, password, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data = agent.update(account)
    
    assert(not data is None)
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
def test_update_photo(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo = Media(shortcode)

    data = agent.update(photo)

    assert(not photo.is_video)

    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
def test_update_photo_set(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo_set = Media(shortcode)
    
    data = agent.update(photo_set)
    
    assert(not photo_set.is_video)
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
def test_update_video(login, password, shortcode):
    agent = AgentAccount(login, password)
    video = Media(shortcode)
    
    data = agent.update(video)
    
    assert(video.is_video)
    
    Media.clear_cache()


@pytest.mark.parametrize("login,password,id", parametrize(locations))
def test_update_location(login, password, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    
    data = agent.update(location)
    
    Location.clear_cache()


@pytest.mark.parametrize("login,password,name", parametrize(tags))
def test_update_tag(login, password, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    
    data = agent.update(tag)
    
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_media_account(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_media(account, count=count)

    assert(min(account.media_count, count) == len(data))
    assert((pointer is None) == (account.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(locations) for i in range(3)]))
def test_get_media_location(login, password, count, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    
    data, pointer = agent.get_media(location, count=count)

    assert(min(location.media_count, count) == len(data))
    assert((pointer is None) == (location.media_count <= count))

    Location.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(tags) for i in range(3)]))
def test_get_media_tag(login, password, count, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    
    data, pointer = agent.get_media(tag, count=count)

    assert(min(tag.media_count, count) == len(data))
    assert((pointer is None) == (tag.media_count <= count))

    Tag.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(photos+photo_sets+videos)]))
def test_get_likes(login, password, count, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    
    data, pointer = agent.get_likes(media, count=count)
    
    assert(min(media.likes_count, count) == len(data))
    assert((pointer is None) == (media.likes_count <= count))

    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_follows(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_follows(account, count=count)

    assert(min(account.follows_count, count) == len(data))
    assert((pointer is None) == (account.follows_count <= count))

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(100, 500) for i in range(3)],
                                     [choice(accounts) for i in range(3)]))
def test_get_followers(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    data, pointer = agent.get_followers(account, count=count)

    assert(min(account.followers_count, count) == len(data))
    assert((pointer is None) == (account.followers_count <= count))

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(100, 500) for i in range(3)]))
def test_get_feed(login, password, count):
    agent = AgentAccount(login, password)
    
    data, pointer = agent.feed(count=count)

    assert(count >= len(data))
    
    Account.clear_cache()


@pytest.mark.parametrize("login,password", [(creds["login"], creds["password"])])
def test_get_stories(login, password):
    agent = AgentAccount(login, password)

    data = agent.stories()

    Account.clear_cache()
    Story.clear_cache()


@pytest.mark.parametrize("login,password,count,username",
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_media_account_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_media(account, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (account.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,id", 
                         parametrize([randint(1, 10)], [choice(locations)]))
def test_get_media_location_pointer(login, password, count, id):
    agent = AgentAccount(login, password)
    location = Location(id)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_media(location, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (location.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()


@pytest.mark.parametrize("login,password,count,name", 
                         parametrize([randint(1, 10)], [choice(tags)]))
def test_get_media_tag_pointer(login, password, count, name):
    agent = AgentAccount(login, password)
    tag = Tag(name)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_media(tag, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (tag.media_count <= count))

    Account.clear_cache()
    Media.clear_cache()
    Tag.clear_cache()


@pytest.mark.parametrize("login,password,count,shortcode",
                         parametrize([randint(1, 10)], [choice(photos+photo_sets+videos)]))
def test_get_likes_pointer(login, password, count, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_likes(media, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (media.likes_count <= count))

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_follows_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_follows(account, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (account.follows_count <= count))

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count,username", 
                         parametrize([randint(1, 10)], [choice(accounts)]))
def test_get_followers_pointer(login, password, count, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.get_followers(account, pointer=pointer)
        data.extend(tmp)

    assert((pointer is None) == (account.followers_count <= count))

    Account.clear_cache()


@pytest.mark.parametrize("login,password,count", parametrize([randint(1, 10)]))
def test_get_feed_pointer(login, password, count):
    agent = AgentAccount(login, password)
    pointer = None
    data = []
    
    for i in range(count):
        tmp, pointer = agent.feed(pointer=pointer)
        data.extend(tmp)

    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photos))
def test_like_unlike_photo(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo = Media(shortcode)
    
    assert(agent.like(photo))
    assert(agent.unlike(photo))
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(photo_sets))
def test_like_unlike_photo_set(login, password, shortcode):
    agent = AgentAccount(login, password)
    photo_set = Media(shortcode)
    
    assert(agent.like(photo_set))
    assert(agent.unlike(photo_set))
    
    Account.clear_cache()
    Media.clear_cache()


@pytest.mark.parametrize("login,password,shortcode", parametrize(videos))
def test_like_unlike_video(login, password, shortcode):
    agent = AgentAccount(login, password)
    video = Media(shortcode)
    
    assert(agent.like(video))
    assert(agent.unlike(video))
    
    Account.clear_cache()
    Media.clear_cache()

@pytest.mark.parametrize("login,password,username", parametrize(accounts))
def test_follow_unfollow(login, password, username):
    agent = AgentAccount(login, password)
    account = Account(username)
    
    assert(agent.follow(account))
    assert(agent.unfollow(account))

    Account.clear_cache()


@pytest.mark.parametrize("login,password,shortcode",
                         parametrize([choice(photos), choice(photo_sets), choice(videos)]))
def test_comment(login, password, shortcode):
    agent = AgentAccount(login, password)
    media = Media(shortcode)
    
    comment = agent.add_comment(media, "test")
    agent.delete_comment(comment)
    
    Account.clear_cache()
    Media.clear_cache()
    Comment.clear_cache()
