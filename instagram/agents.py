import asyncio
import hashlib
import json
import logging
import re
from time import sleep
from urllib.parse import urljoin

import aiohttp
import requests
from requests.exceptions import HTTPError

from .entities import (
    Account,
    Comment,
    Element,
    HasMediaElement,
    Media,
    Location,
    Story,
    Tag,
    UpdatableElement,
)
from .exceptions import (
    AuthException,
    CheckpointException,
    IncorrectVerificationTypeException,
    InstagramException,
    InternetException,
    UnexpectedResponse,
    NotUpdatedElement,
)


class WebAgent:
    API_URL = "https://www.instagram.com/"

    def __init__(self, cookies=None):
        self.rhx_gis = None
        self.csrf_token = None
        self.session = requests.Session()
        if cookies:
            self.session.cookies = requests.cookies.cookiejar_from_dict(cookies)
        self.logger = logging.getLogger(__name__)

    def update(self, obj=None, settings=None):
        if not isinstance(obj, UpdatableElement) and obj is not None:
            raise TypeError("obj must be UpdatableElement type or None")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        settings = {} if settings is None else settings.copy()

        self.logger.debug("Update '%s' started", self if obj is None else obj)

        path = obj.base_url
        if obj is not None:
            path = urljoin(path, getattr(obj, obj.primary_key))

        response = self.get_request(path=path, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            self.rhx_gis = data.get("rhx_gis", "")
            self.csrf_token = data["config"]["csrf_token"]

            if obj is None:
                return None

            data = data["entry_data"]
            for key in obj.entry_data_path:
                data = data[key]
            obj.set_data(data)

            self.logger.debug("Update '%s' was successfull", "self" if obj is None else obj)

            return data
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Update '%s' was unsuccessfull", self if obj is None else obj)
            raise UnexpectedResponse(exception, response.url)

    def get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(obj, HasMediaElement):
            raise TypeError("'obj' must be HasMediaElement type")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.info("Get media '%s' started", obj)

        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        medias = []

        if pointer is None:
            try:
                data = self.update(obj, settings=settings)
                data = data[obj.media_path[-1]]

                page_info = data["page_info"]
                edges = data["edges"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]

                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                else:
                    self.logger.debug("Get media '%s' was successfull", obj)
                    return medias, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get media '%s' was unsuccessfull", obj)
                raise UnexpectedResponse(
                    exception,
                    urljoin(urljoin(self.API_URL, obj.base_url), getattr(obj, obj.primary_key)),
                )

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(obj, Tag):
                data["name"] = "tag_name"
                data["name_value"] = obj.name
            else:
                data["name"] = "id"
                data["name_value"] = obj.id

            response = self.graphql_request(
                query_hash=obj.media_query_hash,
                variables=variables_string.format(**data),
                referer_path=urljoin(obj.base_url, getattr(obj, obj.primary_key)),
                settings=settings,
            )

            try:
                data = response.json()["data"]
                for key in obj.media_path:
                    data = data[key]
                page_info = data["page_info"]
                edges = data["edges"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    sleep(delay)
                else:
                    self.logger.debug("Get media '%s' was successfull", obj)
                    return medias, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get media '%s' was unsuccessfull", obj)
                raise UnexpectedResponse(exception, response.url)

    def get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None):
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
            self.update(media, settings=settings)

        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="1cb6ec562846122743b61e492c85999f",
                variables=variables_string.format(**data),
                referer_path=urljoin(
                    urljoin(self.API_URL, media.base_url),
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = response.json()["data"]["shortcode_media"]["edge_liked_by"]
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
                    count = count-len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    self.logger.debug("Get likes '%s' was successfull", media)
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get likes '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, response.url)

    def get_comments(self, media, pointer=None, count=35, limit=32, delay=0, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
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
                data = self.update(media, settings=settings)
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
                    count = count-len(edges)
                else:
                    self.logger.debug("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get comments '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, media)

        variables_string = '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                referer_path=urljoin(
                    urljoin(self.API_URL, media.base_url),
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = response.json()["data"]["shortcode_media"]["edge_media_to_comment"]
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
                    sleep(delay)
                else:
                    self.logger.debug("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                self.logger.error("Get comments '%s' was unsuccessfull", media)
                raise UnexpectedResponse(exception, response.url)

    def graphql_request(self, query_hash, variables, referer_path, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(referer_path, str):
            raise TypeError("'referer_path' must be str type")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        settings = {} if settings is None else settings.copy()

        if "params" not in settings:
            settings["params"] = {}
        settings["params"]["query_hash"] = query_hash

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            # "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": urljoin(self.API_URL, referer_path),
        })

        return self.get_request(path="/graphql/query/", **settings)

    def action_request(self, path, referer_path, data=None, settings=None):
        if not isinstance(path, str):
            raise TypeError("'path' must be str type")
        if not isinstance(referer_path, str):
            raise TypeError("'referer_path' must be str type")
        if not isinstance(data, dict) and data is not None:
            raise TypeError("'data' must be dict type or None")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        data = {} if data is None else data.copy()
        settings = {} if settings is None else settings.copy()

        headers = {
            "Referer": urljoin(self.API_URL, referer_path),
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-Ajax": "543e5253a719",
            "X-Requested-With": "XMLHttpRequest",
            "X-IG-App-ID": "936619743392459",
        }
        if "headers" in settings:
            settings["headers"].update(headers)
        else:
            settings["headers"] = headers
        if "data" in settings:
            settings["data"].update(data)
        else:
            settings["data"] = data

        return self.post_request(path=path, **settings)

    def get_request(self, path, *args, **kwargs):
        try:
            response = self.session.get(url=urljoin(self.API_URL, path), *args, **kwargs)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)

    def post_request(self, path, *args, **kwargs):
        try:
            response = self.session.post(url=urljoin(self.API_URL, path), *args, **kwargs)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)


class AsyncWebAgent:
    def __init__(self, cookies=None, logger=None):
        self.rhx_gis = None
        self.csrf_token = None
        self.session = aiohttp.ClientSession(cookies=cookies)
        self.logger = logger

    async def delete(self):
        await self.session.close()

    async def update(self, obj=None, settings=None):
        if not self.logger is None:
            self.logger.info("Update '%s' started", "self" if obj is None else obj)
        if not isinstance(obj, UpdatableElement) and not obj is None:
            raise TypeError("obj must be UpdatableElement type or None")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        query = "https://www.instagram.com/"
        if not obj is None:
            query += obj.base_url + getattr(obj, obj.primary_key)

        response = await self.get_request(query, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                await response.text(),
            )
            data = json.loads(match.group(1))
            self.rhx_gis = data.get("rhx_gis", "")
            self.csrf_token = data["config"]["csrf_token"]

            if obj is None:
                return None

            data = data["entry_data"]
            for key in obj.entry_data_path:
                data = data[key]
            obj.set_data(data)

            if not self.logger is None:
                self.logger.info("Update '%s' was successfull", "self" if obj is None else obj)
            return data
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.exception(
                    "Update '%s' was unsuccessfull: %s",
                    "self" if obj is None else obj,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    async def get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not self.logger is None:
            self.logger.info("Get media '%s' started", obj)
        if not isinstance(obj, HasMediaElement):
            raise TypeError("'obj' must be HasMediaElement type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        variables_string = '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        medias = []

        if pointer is None:
            try:
                data = await self.update(obj, settings=settings)
                data = data[obj.media_path[-1]]

                page_info = data["page_info"]
                edges = data["edges"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]

                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                else:
                    if not self.logger is None:
                        self.logger.info("Get media '%s' was successfull", obj)
                    return medias, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get media '%s' was unsuccessfull: %s", obj, str(exception))
                raise UnexpectedResponse(
                    exception,
                    "https://www.instagram.com/" + obj.base_url + getattr(obj, obj.primary_key),
                )

        while True:
            data = {"after": pointer, "first": min(limit, count)}
            if isinstance(obj, Tag):
                data["name"] = "tag_name"
                data["name_value"] = obj.name
            else:
                data["name"] = "id"
                data["name_value"] = obj.id

            response = await self.graphql_request(
                query_hash=obj.media_query_hash,
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    obj.base_url,
                    getattr(obj, obj.primary_key),
                ),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]
                for key in obj.media_path:
                    data = data[key]
                page_info = data["page_info"]
                edges = data["edges"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    if isinstance(obj, Account):
                        m.likes_count = node["edge_media_preview_like"]["count"]
                        m.owner = obj
                    else:
                        m.likes_count = node["edge_liked_by"]
                    obj.media.add(m)
                    medias.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    await asyncio.sleep(delay)
                else:
                    if not self.logger is None:
                        self.logger.info("Get media '%s' was successfull", obj)
                    return medias, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get media '%s' was unsuccessfull: %s", obj, str(exception))
                raise UnexpectedResponse(exception, response.url)

    async def get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None):
        if not self.logger is None:
            self.logger.info("Get likes '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        if media.id is None:
            await self.update(media, settings=settings)

        if pointer:
            variables_string = '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        while True:
            data = {"shortcode": media.code, "first": min(limit, count)}
            if pointer:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="1cb6ec562846122743b61e492c85999f",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    media.base_url,
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["shortcode_media"]["edge_liked_by"]
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
                    count = count-len(edges)
                    variables_string = \
                        '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    if not self.logger is None:
                        self.logger.info("Get likes '%s' was successfull", media)
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get likes '%s' was unsuccessfull: %s", media, str(exception))
                raise UnexpectedResponse(exception, response.url)

    async def get_comments(self, media, pointer=None, count=35, limit=32, delay=0, settings=None):
        if not self.logger is None:
            self.logger.info("Get comments '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        comments = []

        if pointer is None:
            try:
                data = await self.update(media, settings=settings)
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

                if len(edges) < count and not pointer is None:
                    count = count - len(edges)
                else:
                    if not self.logger is None:
                        self.logger.info("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get comments '%s' was unsuccessfull: %s",
                        media,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, media)

        variables_string =  '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = await self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    media.base_url,
                    getattr(media, media.primary_key),
                ),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["shortcode_media"]["edge_media_to_comment"]
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
                    if not self.logger is None:
                        self.logger.info("Get comments '%s' was successfull", media)
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get comments '%s' was unsuccessfull: %s",
                        media,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, response.url)

    async def graphql_request(self, query_hash, variables, referer_path, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(referer_path, str):
            raise TypeError("'referer_path' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = {} if settings is None else settings.copy()

        if "params" not in settings:
            settings["params"] = {}
        settings["params"]["query_hash"] = query_hash

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            # "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": urljoin(self.API_URL, referer_path),
        })

        return await self.get_request(path="/graphql/query/", **settings)

    async def action_request(self, path, referer_path, data=None, settings=None):
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

        headers = {
            "Referer": urljoin(self.API_URL, referer_path),
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-AJAX": "1",
            "X-Requested-With": "XMLHttpRequest",
        }
        if "headers" in settings:
            settings["headers"].update(headers)
        else:
            settings["headers"] = headers
        if "data" in settings:
            settings["data"].update(data)
        else:
            settings["data"] = data

        return await self.post_request(path=path, **settings)

    async def get_request(self, path, *args, **kwargs):
        try:
            return await self.session.get(url=urljoin(self.API_URL, path), *args, **kwargs)
        except aiohttp.ClientResponseError as exception:
            raise InternetException(exception)

    async def post_request(self, path, *args, **kwargs):
        try:
            return await self.session.post(url=urljoin(self.API_URL, path), *args, **kwargs)
        except aiohttp.ClientResponseError as exception:
            raise InternetException(exception)


class WebAgentAccount(Account, WebAgent):
    def __init__(self, username, cookies=None, logger=None):
        if not isinstance(username, str):
            raise TypeError("'username' must be str type")

        Account.__init__(self, username)
        WebAgent.__init__(self, cookies=cookies, logger=logger)

    def auth(self, password, settings=None):
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        settings = {} if settings is None else settings.copy()

        self.logger.debug("Auth started")

        self.update(settings=settings)

        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            # "X_Instagram-AJAX": "ee72defd9231",
            "X-CSRFToken": self.csrf_token,
            "Referer": self.API_URL,
        })
        if "data" not in settings:
            settings["data"] = {}
        settings["data"].update({"username": self.username, "password": password})

        try:
            response = self.post_request(
                path=urljoin(self.API_URL, "accounts/login/ajax/"),
                **settings,
            )
        except InternetException as exception:
            response = exception.response

        try:
            data = response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                data = self.checkpoint_handle(
                    checkpoint_path=data.get("checkpoint_url"),
                    settings=settings,
                )
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=urljoin(self.API_URL, data.get("checkpoint_url")),
                    navigation=data["navigation"],
                    types=data["types"],
                )
        except (ValueError, KeyError) as exception:
            self.logger.exception("Auth was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)

        self.logger.debug("Auth was successfully")

    def checkpoint_handle(self, checkpoint_path, settings=None):
        self.logger.debug("Handle checkpoint page for '%s' started", self)

        response = self.get_request(path=checkpoint_path, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            data = data["entry_data"]["Challenge"][0]

            navigation = {
                key: urljoin(self.API_URL, value) for key, value in data["navigation"].items()
            }

            data = data["extraData"]["content"]
            data = list(filter(lambda item: item["__typename"] == "GraphChallengePageForm", data))
            data = data[0]["fields"][0]["values"]
            types = []
            for d in data:
                types.append({"label": d["label"].lower().split(":")[0], "value": d["value"]})
            self.logger.debug("Handle checkpoint page for '%s' was successfull", self)
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Handle checkpoint page for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    def checkpoint_send(self, checkpoint_path, forward_path, choice, settings=None):
        self.logger.debug("Send verify code for '%s' started", self)

        response = self.action_request(
            path=forward_path,
            referer_path=checkpoint_path,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = response.json()["navigation"]
            self.logger.debug("Send verify code for '%s' was successfully", self)

            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            self.logger.exception("Send verify code by %s to '%s' was unsuccessfully", type, self)
            raise UnexpectedResponse(exception, response.url)

    def checkpoint_replay(self, forward_path, replay_path, settings=None):
        self.logger.debug("Resend verify code for '%s' started", self)

        response = self.action_request(
            path=replay_path,
            referer_path=forward_path,
            settings=settings,
        )
        try:
            navigation = response.json()["navigation"]
            self.logger.debug("Resend verify code for '%s' was successfull", self)
            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Resend verify code for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    def checkpoint(self, path, code, settings=None):
        self.logger.debug("Verify account '%s' started", self)

        response = self.action_request(
            path=path,
            referer_path=path,
            data={"security_code": code},
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            self.logger.debug("Verify account '%s' was successfull", self)
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.error("Verify account '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return WebAgent.update(self, obj=obj, settings=settings)

    def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return WebAgent.get_media(self, obj=obj, pointer=pointer, count=count, limit=limit,
                                  delay=delay, settings=settings)

    def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get '%s' follows started", account)

        if account is None:
            account = self

        if account.id is None:
            self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.base_url, getattr(account, account.primary_key)),
                settings=settings,
            )

            try:
                data = response.json()["data"]["user"]["edge_follow"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.follows_count = data["count"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.follows.add(a)
                    follows.append(a)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    self.logger.debug("Get '%s' follows was successfully", account)
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' follows was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get '%s' followers started", account)

        if account is None:
            account = self
        if account.id is None:
            self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.base_url, getattr(account, account.primary_key)),
                settings=settings,
            )

            try:
                data = response.json()["data"]["user"]["edge_followed_by"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.followers_count = data["count"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.followers.add(a)
                    followers.append(a)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    sleep(delay)
                else:
                    self.logger.debug("Get '%s' followers was successfully", account)
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' followers was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    def stories(self, settings=None):
        self.logger.debug("Get stories started")

        response = self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer_path=urljoin(self.base_url, getattr(self, self.primary_key)),
            settings=settings,
        )

        try:
            data = response.json()["data"]["user"]["feed_reels_tray"]["edge_reels_tray_to_reel"]
            self.logger.debug("Get stories was successfully")
            return [Story(edge["node"]["id"]) for edge in data["edges"]]
        except (ValueError, KeyError) as exception:
            self.logger.exception("Get stories was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)

    def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get feed started")

        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        while True:
            response = self.graphql_request(
                query_hash="485c25657308f08317c1e4b967356828",
                variables=variables_string.format(
                    after=pointer,
                    first=min(limit, count),
                ) if pointer else "{}",
                referer_path=urljoin(self.base_url, getattr(self, self.primary_key)),
                settings=settings,
            )

            try:
                data = response.json()["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if "shortcode" not in node:
                        length -= 1
                        continue
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    feed.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if length < count and page_info["has_next_page"]:
                    count -= length
                    sleep(delay)
                else:
                    self.logger.debug("Get feed was successfully")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get feed was unsuccessfully")
                raise UnexpectedResponse(exception, response.url)

    def like(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Like '%s' started", media)

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer_path=urljoin(media.base_url, media.code),
            path=f"/web/likes/{media.id}/like/",
            settings=settings,
        )

        try:
            self.logger.debug("Like '%s' was successfully", media)
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    def unlike(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unlike '%s' started", media)

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            path=f"/web/likes/{media.id}/unlike/",
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            self.logger.debug("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    def save(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Save '%s' started", media)

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            path=urljoin("/web/save/%s/save/", media.id),
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            self.logger.debug("Save '%s' was successfully", media)
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            self.logger.exception("Save '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    def unsave(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unsave '%s' started", media)

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            path=f"/web/save/{media.id}/unsave/",
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            self.logger.debug("Unsave '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unsave '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    def add_comment(self, media, text, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        self.logger.info("Comment '%s' started")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            path=f"/web/comments/{media.id}/add/",
            referer_path=urljoin(media.base_url, media.code),
            data={"comment_text": text},
            settings=settings,
        )

        try:
            data = response.json()
            if data["status"] == "ok":
                comment = Comment(
                    data["id"],
                    media=media,
                    owner=self,
                    text=data["text"],
                    created_at=data["created_time"],
                )
            else:
                comment = None
            self.logger.debug("Comment '%s' was successfully", media)
            return comment
        except (ValueError, KeyError) as exception:
            self.logger.exception("Comment '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    def delete_comment(self, comment, settings=None):
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        self.logger.debug("Delete comment '%s' started", comment)

        if comment.media.id is None:
            self.update(comment.media, settings=settings)

        response = self.action_request(
            path=f"/web/comments/{comment.media.id}/delete/{comment.id}/",
            referer_path=urljoin(comment.media.base_url, comment.media.code),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if result:
                del comment
            self.logger.debug("Delete comment '%s' was successfully", comment)
        except (ValueError, KeyError) as exception:
            self.logger.exception("Delete comment '%s' was unsuccessfully", comment)
            raise UnexpectedResponse(exception, response.url)

    def follow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Follow to '%s' started", account)

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            path=f"/web/friendships/{account.id}/follow/",
            referer_path=urljoin(account.base_url, account.username),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            self.logger.debug("Follow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Follow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)

    def unfollow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Unfollow to '%s' started", account)

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            path=f"/web/friendships/{account.id}/unfollow/",
            referer_path=urljoin(account.base_url, account.username),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            self.logger.debug("Unfollow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unfollow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)


class AsyncWebAgentAccount(Account, AsyncWebAgent):
    def __init__(self, username, cookies=None, logger=None):
        if not isinstance(username, str):
            raise TypeError("'username' must be str type")

        Account.__init__(self, username)
        AsyncWebAgent.__init__(self, cookies=cookies, logger=logger)

    async def delete(self):    
        await self.session.close()

    async def auth(self, password, settings=None):
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and settings is not None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        self.logger.debug("Auth started")

        await self.update(settings=settings)

        if "headers" not in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            # "X_Instagram-AJAX": "ee72defd9231",
            "X-CSRFToken": self.csrf_token,
            "Referer": self.API_URL,
        })
        if "data" not in settings:
            settings["data"] = {}
        settings["data"].update({"username": self.username, "password": password})

        response = await self.post_request(
            path="/accounts/login/ajax/",
            **settings,
        )

        try:
            data = await response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                data = await self.checkpoint_handle(
                    path=data.get("checkpoint_url"),
                    settings=settings,
                )
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=urljoin(self.API_URL, data.get("checkpoint_url")),
                    navigation=data["navigation"],
                    types=data["types"],
                )
        except (ValueError, KeyError) as exception:
            self.logger.exception("Auth was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)
        self.logger.debug("Auth was successfully")

    async def checkpoint_handle(self, path, settings=None):
        self.logger.debug("Handle checkpoint page for '%s' started", self)

        response = await self.get_request(url, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                await response.text(),
            )
            data = json.loads(match.group(1))
            data = data["entry_data"]["Challenge"][0]

            navigation = {
                key: urljoin(self.API_URL, value) for key, value in data["navigation"].items()
            }

            data = data["extraData"]["content"]
            data = list(filter(lambda item: item["__typename"] == "GraphChallengePageForm", data))
            data = data[0]["fields"][0]["values"]
            types = []
            for d in data:
                types.append({"label": d["label"].lower().split(":")[0], "value": d["value"]})
            self.logger.debug("Handle checkpoint page for '%s' was successfull")
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Handle checkpoint page for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint_send(self, checkpoint_path, forward_path, choice, settings=None):
        self.logger.debug("Send verify code for '%s' started", self)

        response = await self.action_request(
            path=forward_path,
            referer_path=checkpoint_path,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = (await response.json())["navigation"]
            self.logger.debug("Send verify code for '%s' was successfully", self)
            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            self.logger.exception("Send verify code by %s to '%s' was unsuccessfully", type, self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint_replay(self, forward_path, replay_path, settings=None):
        self.logger.debug("Resend verify code for '%s' started", self)

        response = await self.action_request(
            path=replay_path,
            referer_path=forward_path,
            settings=settings,
        )
        try:
            navigation = (await response.json())["navigation"]
            self.logger.debug("Resend verify code for '%s' was successfull", self)
            return {
                key: urljoin(self.API_URL, value) for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Resend verify code for '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def checkpoint(self, path, code, settings=None):
        self.logger.debug("Verify account '%s' started", self)

        response = await self.action_request(
            path=path,
            referer_path=path,
            data={"security_code": code},
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Verify account '%s' was successfull", self)
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            self.logger.exception("Verify account '%s' was unsuccessfull", self)
            raise UnexpectedResponse(exception, response.url)

    async def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return await AsyncWebAgent.update(self, obj=obj, settings=settings)

    async def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return await AsyncWebAgent.get_media(self, obj=obj, pointer=pointer, count=count,
                                             limit=limit, delay=delay, settings=settings)

    async def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0,
                          settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(count, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get '%s' follows started", account)

        if account is None:
            account = self
        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.base_url, getattr(account, account.primary_key)),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_follow"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.follows_count = data["count"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.follows.add(a)
                    follows.append(a)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get '%s' follows was successfully", account)
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' follows was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    async def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0,
                            settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type or None")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get '%s' followers started", account)

        if account is None:
            account = self
        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if pointer is not None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                referer_path=urljoin(account.base_url, getattr(account, account.primary_key)),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_followed_by"]
                edges = data["edges"]
                page_info = data["page_info"]
                account.followers_count = data["count"]

                for index in range(min(len(edges), count)):
                    node = edges[index]["node"]
                    a = Account(node["username"])
                    a.id = node["id"]
                    a.profile_pic_url = node["profile_pic_url"]
                    a.is_verified = node["is_verified"]
                    a.full_name = node["full_name"]
                    account.followers.add(a)
                    followers.append(a)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if len(edges) < count and page_info["has_next_page"]:
                    count = count - len(edges)
                    variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get '%s' followers was successfully", account)
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get '%s' followers was unsuccessfully", account)
                raise UnexpectedResponse(exception, response.url)

    async def stories(self, settings=None):
        response = await self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer_path=urljoin(self.base_url, getattr(self, self.primary_key)),
            settings=settings,
        )

        self.logger.debug("Get stories started")

        try:
            data = (await response.json())["data"]["user"]["feed_reels_tray"]
            data = data["edge_reels_tray_to_reel"]
            result = [Story(edge["node"]["id"]) for edge in data["edges"]]
            self.logger.debug("Get stories was successfully")
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Get stories was unsuccessfully")
            raise UnexpectedResponse(exception, response.url)

    async def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not isinstance(pointer, str) and pointer is not None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

        self.logger.debug("Get feed started")

        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        while True:
            response = await self.graphql_request(
                query_hash="485c25657308f08317c1e4b967356828",
                variables=variables_string.format(
                    after=pointer,
                    first=min(limit, count),
                ) if pointer else "{}",
                referer_path=urljoin(self.base_url, getattr(self, self.post_request)),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if "shortcode" not in node:
                        length -= 1
                        continue
                    m = Media(node["shortcode"])
                    m.set_data(node)
                    feed.append(m)

                pointer = page_info["end_cursor"] if page_info["has_next_page"] else None

                if length < count and page_info["has_next_page"]:
                    count -= length
                    await asyncio.sleep(delay)
                else:
                    self.logger.debug("Get feed was successfully")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                self.logger.exception("Get feed was unsuccessfully")
                raise UnexpectedResponse(exception, response.url)

    async def like(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Like '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/likes/{media.id}/like/",
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def unlike(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unlike '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/likes/{media.id}/unlike/",
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Like '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def save(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Save '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            path=f"/web/save/{media.id}/save/",
            referer_path=urljoin(media.base_url, media.code),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Save '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Save '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def unsave(self, media, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        self.logger.debug("Unsave '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(media.base_url, media.code),
            path=f"/web/save/{media.id}/unsave/",
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Unsave '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unsave '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def add_comment(self, media, text, settings=None):
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        self.logger.debug("Comment '%s' started", media)

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(media.base_url, media.code),
            path=f"/web/comments/{media.id}/add/",
            data={"comment_text": text},
            settings=settings,
        )

        try:
            data = await response.json()
            if data["status"] == "ok":
                comment = Comment(
                    data["id"],
                    media=media,
                    owner=self,
                    text=data["text"],
                    created_at=data["created_time"],
                )
            else:
                comment = None
            self.logger.debug("Comment '%s' was successfully", media)
            return comment
        except (ValueError, KeyError) as exception:
            self.logger.exception("Comment '%s' was unsuccessfully", media)
            raise UnexpectedResponse(exception, response.url)

    async def delete_comment(self, comment, settings=None):
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        self.logger.debug("Delete comment '%s' started", comment)

        if comment.media.id is None:
            await self.update(comment.media, settings=settings)

        response = await self.action_request(
            referer_path=urljoin(comment.media.base_url, comment.media.code),
            path=f"/web/comments/{comment.media.id}/delete/{comment.id}/",
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if result:
                del comment
            self.logger.debug("Delete comment '%s' was successfully", comment)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Delete comment '%s' was unsuccessfully", comment)
            raise UnexpectedResponse(exception, response.url)

    async def follow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Follow to '%s' started", account)

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            path=f"/web/friendships/{account.id}/follow/",
            referer_path=urljoin(account.base_url, account.username),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Follow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Follow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)

    async def unfollow(self, account, settings=None):
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        self.logger.debug("Unfollow to '%s' started", account)

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            path=f"/web/friendships/{account.id}/unfollow/",
            referer_path=urljoin(account.base_url, account.username),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            self.logger.debug("Unfollow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            self.logger.exception("Unfollow to '%s' was unsuccessfully", account)
            raise UnexpectedResponse(exception, response.url)


# https://github.com/ping/instagram_private_api
# class MobileAgentAccount(Account):
#     API_URL = "https://i.instagram.com/api/"
#     SIG_KEY = "19ce5f445dbfd9d29c59dc2a78c616a7fc090a8e018b9267bc4240a30244c53b"


# class AsyncMobileAgentAccount(MobileAgentAccount):
#     pass
