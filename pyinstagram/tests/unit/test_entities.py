from pyinstagram.entities import Account, Comment, Location, Media, Story, Tag
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
def test_account_creation(id):
    account = Account(id)
    assert getattr(account, account.primary_key) == id
    assert len(Account.cache) == 1 and Account.cache[id] is account


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_media_creation(id):
    media = Media(id)
    assert getattr(media, media.primary_key) == id
    assert len(Media.cache) == 1 and Media.cache[id] is media


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_location_creation(id):
    location = Location(id)
    assert getattr(location, location.primary_key) == id
    assert len(Location.cache) == 1 and Location.cache[id] is location


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_tag_creation(id):
    tag = Tag(id)
    assert getattr(tag, tag.primary_key) == id
    assert len(Tag.cache) == 1 and Tag.cache[id] is tag


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_comment_creation(id):
    account = Account("test")
    media = Media("test")
    comment = Comment(id, media=media, owner=account, text="test", created_at=0)
    assert getattr(comment, comment.primary_key) == id
    assert comment.media is media
    assert comment.owner is account
    assert comment.text == "test"
    assert comment.created_at == 0
    assert len(Comment.cache) == 1 and Comment.cache[id] is comment


@pytest.mark.parametrize("id", [id() for _ in range(3)])
def test_story_creation(id):
    story = Story(id)
    assert getattr(story, story.primary_key) == id
    assert len(Story.cache) == 1 and Story.cache[id] is story
