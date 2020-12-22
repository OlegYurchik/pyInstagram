import asyncio
import hashlib
import json
import logging
import re
from typing import (
    List,
    Optional,
)
from urllib.parse import urljoin

import aiohttp

from .utils import sync
from ..entities import (
    Account,
    Comment,
    HasMediaEntity,
    Media,
    Tag,
    UpdatableEntity,
)


class AsyncWebAgent:
    API_URL = "https://www.instagram.com/"

    def __init__(self, cookies=None):
        self.rhx_gis = None
        self.csrf_token = None
        self.session = aiohttp.ClientSession(cookies=cookies)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _get_shared_data(content: str):
        match = re.search(
            r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
            content,
        )
        if match:
            return json.loads(match.group(1))

    @staticmethod
    def _get_medias_from_edges(parent: HasMediaEntity, edges: list, count: int):
        medias = []
        for index in range(min(len(edges), count)):
            node = edges[index]["node"]
            media = Media(node["shortcode"])
            media.set_web_data(node)
            if isinstance(parent, Account):
                media.owner = parent
            medias.append(media)
            parent.media.add(media)
        return medias

    async def _get_request(self, path: str, *args, **kwargs) -> str:
        if not isinstance(path, str):
            raise TypeError("'path' must be str type")
        print("URL:", urljoin(self.API_URL, path))
        response = await self.session.get(url=urljoin(self.API_URL, path), *args, **kwargs)
        return await response.text()

    async def _post_request(self, path: str, *args, **kwargs) -> str:
        if not isinstance(path, str):
            raise TypeError("'path' must be str type")
        response = await self.session.post(url=urljoin(self.API_URL, path), *args, **kwargs)
        return await response.text()

    async def _graphql_request(self, query_hash: str, variables: str, referer_path: str,
                               settings: Optional[dict] = None) -> str:
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(referer_path, str):
            raise TypeError("'referer_path' must be str type")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")

        settings = {} if settings is None else settings.copy()

        settings["params"] = {
            "query_hash": query_hash,
            "variables": variables,
        }
        gis = "%s:%s" % (self.rhx_gis, variables)
        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            # "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": urljoin(self.API_URL, referer_path),
        })

        return await self._get_request(path="/graphql/query/", **settings)

    async def _action_request(self, path: str, referer_path: str, data: Optional[dict] = None,
                              settings: Optional[dict] = None) -> str:
        if not isinstance(path, str):
            raise TypeError("'path' must be str type")
        if not isinstance(referer_path, str):
            raise TypeError("'referer_oath' must be str type")
        if not isinstance(data, dict) and data is not None:
            raise TypeError("'data' must be dict type or None")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")

        data = {} if data is None else data.copy()
        settings = {} if settings is None else settings.copy()

        settings["data"] = data
        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "Referer": urljoin(self.API_URL, referer_path),
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-AJAX": "1",
            "X-Requested-With": "XMLHttpRequest",
        })

        return await self._post_request(path=path, **settings)

    async def update(self, entity: Optional[UpdatableEntity] = None,
                     settings: Optional[dict] = None) -> dict:
        if not isinstance(entity, UpdatableEntity) and entity is not None:
            raise TypeError("'entity' must be UpdatableEntity type or None")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")

        settings = {} if settings is None else settings.copy()

        self.logger.debug("Update '%s' started", entity)

        path = "" if entity is None else entity.get_web_path()
        print("PATH:", path)
        content = await self._get_request(path=path, **settings)
        print("CONTENT:", content[:500])
        data = self._get_shared_data(content=content)

        self.rhx_gis = data.get("rhx_gis", "")
        self.csrf_token = data["config"]["csrf_token"]

        if entity is None:
            return data

        data = entity.get_from_web_entry_data_path(data["entry_data"])
        entity.set_web_data(data)

        self.logger.debug("Update '%s' was successfull", entity)

        return data

    async def get_media(self, entity: HasMediaEntity, pointer: Optional[str] = None,
                        count: int = 12, limit: int = 50, delay: float = 0,
                        settings: Optional[dict] = None) -> (List[Media], str):
        if not isinstance(entity, HasMediaEntity):
            raise TypeError("'entity' must be HasMediaEntity type")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.info("Get media '%s' started", entity)

        if pointer is None:
            data = await self.update(entity=entity, settings=settings)
            data = data[entity.web_media_path[-1]]

            page_info = data["page_info"]
            edges = data["edges"]

            medias = self._get_medias_from_edges(parent=entity, edges=edges, count=count)

            pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

            if len(medias) < count and page_info["has_next_page"]:
                count -= len(edges)
            else:
                self.logger.debug("Get media '%s' was successfull", entity)
                return medias, pointer

        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(entity, Tag):
                data["name"] = "tag_name"
                data["name_value"] = entity.name
            else:
                data["name"] = "id"
                data["name_value"] = entity.id

            content = await self._graphql_request(
                query_hash=entity.web_media_query_hash,
                variables=variables_string.format(**data),
                referer_path=urljoin(entity.web_base_path, getattr(entity, entity.primary_key)),
                settings=settings,
            )
            data = json.loads(content)
            data = entity.get_from_web_media_path(data["data"])
            page_info = data["page_info"]
            edges = data["edges"]

            medias = self._get_medias_from_edges(parent=entity, edges=edges, count=count)

            pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

            if len(edges) < count and page_info["has_next_page"]:
                count -= len(edges)
                await asyncio.sleep(delay)
            else:
                self.logger.debug("Get media '%s' was successfull", entity)
                return medias, pointer

    async def get_likes(self, media: Media, pointer: Optional[str] = None, count: int = 20,
                        limit: int = 50, delay: float = 0, settings: Optional[dict] = None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get likes '%s' started", media)

        if media.id is None:
            await self.update(entity=media, settings=settings)

        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            response = await self._graphql_request(
                query_hash="1cb6ec562846122743b61e492c85999f",
                variables=variables_string.format(**data),
                referer_path=urljoin(
                    urljoin(self.API_URL, media.web_base_path),
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = json.loads(response)["data"]["shortcode_media"]["edge_liked_by"]
                edges = data["edges"]
                page_info = data["page_info"]
                media.likes_count = data["count"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    account = Account(node["username"])
                    account.id = node["id"]
                    account.profile_pic_url = node["profile_pic_url"]
                    account.is_verified = node["is_verified"]
                    account.full_name = node["full_name"]
                    media.likes.add(account)
                    likes.append(account)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get likes '%s' was successfull", media)
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get likes '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, response.url)

    async def get_comments(self, media: Media, pointer: Optional[str] = None, count: int = 35,
                           limit: int = 32, delay: float = 0, settings: Optional[dict] = None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get comments '%s' started", media)

        comments = []

        if pointer is None:
            try:
                data = await self.update(entity=media, settings=settings)
                if "edge_media_to_comment" in data:
                    data = data["edge_media_to_comment"]
                else:
                    data = data["edge_media_to_parent_comment"]
                edges = data["edges"]
                page_info = data["page_info"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    c = Comment(node["id"], media=media,
                                owner=Account(node["owner"]["username"]),
                                text=node["text"],
                                created_at=node["created_at"])
                    media.comments.add(c)
                    comments.append(c)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and pointer is not None:
                    count = count - len(edges)
                else:
                    self.logger.debug("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get comments '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, media)

        variables_string = '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = await self._graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                referer_path=urljoin(
                    urljoin(self.API_URL, media.web_base_path),
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = json.loads(response)["data"]["shortcode_media"]["edge_media_to_comment"]
                media.comments_count = data["count"]
                edges = data["edges"]
                page_info = data["page_info"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    c = Comment(node["id"],
                                media=media,
                                owner=Account(node["owner"]["username"]),
                                text=node["text"],
                                created_at=node["created_at"])
                    media.comments.add(c)
                    comments.append(c)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                self.logger.error("Get comments '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, response.url)
