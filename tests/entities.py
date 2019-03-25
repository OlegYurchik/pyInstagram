from instagram.entities import Account, Comment, Location, Media, Story, Tag
import pytest
from random import randint, choice
from string import ascii_uppercase, ascii_lowercase, digits


def setup_function():
    Account.clear_cache()
    Comment.clear_cache()
    Location.clear_cache()
    Media.clear_cache()
    Story.clear_cache()
    Tag.clear_cache()


def id():
    return "".join(
        choice(ascii_uppercase + ascii_lowercase + digits) for _ in range(randint(1, 50))
    )


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_account(id):
    account = Account(id)
    assert Account.cache == {id: account}

    Account.clear_cache()
    assert Account.cache == dict()


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_media(id):
    media = Media(id)
    assert Media.cache == {id: media}

    Media.clear_cache()    
    assert Media.cache == dict()


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_location(id):
    location = Location(id)
    assert Location.cache == {id: location}

    Location.clear_cache()
    assert Location.cache == dict()


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_tag(id):
    tag = Tag(id)
    assert Tag.cache == {id: tag}

    Tag.clear_cache()
    assert Tag.cache == dict()


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_comment(id):
    account = Account("test")
    media = Media("test")
    comment = Comment(id, media=media, owner=account, text="test", created_at=0)
    assert Comment.cache == {id: comment}  

    Comment.clear_cache()
    assert Comment.cache == dict()
    assert Media.cache == {"test": media}
    assert Account.cache == {"test": account}


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_clear_cache_story(id):
    story = Story(id)
    assert Story.cache == {id: story}
    
    Story.clear_cache()
    assert Story.cache == dict()
