from .async_web_account_agent import AsyncWebAccountAgent
from .utils import sync


class WebAccountAgent(AsyncWebAccountAgent):
    login = sync(AsyncWebAccountAgent.login)
    checkpoint_handle = sync(AsyncWebAccountAgent.checkpoint_handle)
    checkpoint_send = sync(AsyncWebAccountAgent.checkpoint_send)
    checkpoint_replay = sync(AsyncWebAccountAgent.checkpoint_replay)
    checkpoint = sync(AsyncWebAccountAgent.checkpoint)
    update = sync(AsyncWebAccountAgent.update)
    get_media = sync(AsyncWebAccountAgent.get_media)
    get_follows = sync(AsyncWebAccountAgent.get_follows)
    get_followers = sync(AsyncWebAccountAgent.get_followers)
    stories = sync(AsyncWebAccountAgent.stories)
    feed = sync(AsyncWebAccountAgent.feed)
    like = sync(AsyncWebAccountAgent.like)
    unlike = sync(AsyncWebAccountAgent.unlike)
    save = sync(AsyncWebAccountAgent.save)
    unsave = sync(AsyncWebAccountAgent.unsave)
    add_comment = sync(AsyncWebAccountAgent.add_comment)
    delete_comment = sync(AsyncWebAccountAgent.delete_comment)
    follow = sync(AsyncWebAccountAgent.follow)
    unfollow = sync(AsyncWebAccountAgent.unfollow)
