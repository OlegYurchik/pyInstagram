from .async_web_agent import AsyncWebAgent
from .utils import sync


class WebAgent(AsyncWebAgent):
    update = sync(AsyncWebAgent.update)
    get_media = sync(AsyncWebAgent.get_media)
    get_likes = sync(AsyncWebAgent.get_likes)
    get_comments = sync(AsyncWebAgent.get_comments)
