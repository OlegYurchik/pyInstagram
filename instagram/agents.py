import aiohttp
import asyncio
import hashlib
from .entities import (Account, Comment, Element, HasMediaElement,Media, Location, Story, Tag,
                       UpdatableElement)
from .exceptions import (AuthException, CheckpointException, ExceptionManager,
                         IncorrectVerificationTypeException, InstagramException,
                         InternetException, UnexpectedResponse, NotUpdatedElement)
import json
import re
import requests
from requests.exceptions import HTTPError
from time import sleep


exception_manager = ExceptionManager()


class WebAgent:
    def __init__(self, cookies=None, logger=None):
        self.rhx_gis = None
        self.csrf_token = None
        self.session = requests.Session()
        if cookies:
            self.session.cookies = requests.cookies.cookiejar_from_dict(cookies)
        self.logger = logger

    @exception_manager.decorator
    def update(self, obj=None, settings=None):
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

        response = self.get_request(query, **settings)

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
                data=data[key]
            obj.set_data(data)

            if not self.logger is None:
                self.logger.info("Update '%s' was successfull", "self" if obj is None else obj)
            return data
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Update '%s' was unsuccessfull: %s",
                    "self" if obj is None else obj,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_media(self, obj, pointer=None, count=12, limit=50, delay=0, settings=None):
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

            response = self.graphql_request(
                query_hash=obj.media_query_hash,
                variables=variables_string.format(**data),
                referer="https://instagram.com/" + obj.base_url + getattr(obj, obj.primary_key),
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
                    if not self.logger is None:
                        self.logger.info("Get media '%s' was successfull", obj)
                    return medias, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get media '%s' was unsuccessfull: %s", obj, str(exception))
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_likes(self, media, pointer=None, count=20, limit=50, delay=0, settings=None):
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
                referer="https://instagram.com/%s%s" % (
                    media.base_url,
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
                    if not self.logger is None:
                        self.logger.info("Get likes '%s' was successfull", media)
                    return likes, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get likes '%s' was unsuccessfull: %s", media, str(exception))
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_comments(self, media, pointer=None, count=35, limit=32, delay=0, settings=None):
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

                if len(edges) < count and not pointer is None:
                    count = count-len(edges)
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

        variables_string = '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    media.base_url,
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

    def graphql_request(self, query_hash, variables, referer, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        if not "params" in settings:
            settings["params"] = dict() 
        settings["params"].update({"query_hash": query_hash})

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if not "headers" in settings:
            settings["headers"] = dict()
        settings["headers"].update({
            # "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
        })

        return self.get_request("https://www.instagram.com/graphql/query/", **settings)

    def action_request(self, referer, url, data=None, settings=None):
        if not isinstance(referer, str):
            raise TypeError("'referer' must be str type")
        if not isinstance(url, str):
            raise TypeError("'url' must be str type")
        if not isinstance(data, dict) and not data is None:
            raise TypeError("'data' must be dict type or None")
        data = dict() if data is None else data.copy()
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        headers = {
            "Referer": referer,
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-Ajax": "1",
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

        return self.post_request(url, **settings)

    def get_request(self, *args, **kwargs):
        try:
            response = self.session.get(*args, **kwargs)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)

    def post_request(self, *args, **kwargs):
        try:
            response = self.session.post(*args, **kwargs)
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

    @exception_manager.decorator
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

    @exception_manager.decorator
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

    @exception_manager.decorator
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

    @exception_manager.decorator
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

    async def graphql_request(self, query_hash, referer, variables, settings=None):
        if not isinstance(query_hash, str):
            raise TypeError("'query_hash' must be str type")
        if not isinstance(variables, str):
            raise TypeError("'variables' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        if not "params" in settings:
            settings["params"] = dict() 
        settings["params"].update({"query_hash": query_hash})

        settings["params"]["variables"] = variables
        gis = "%s:%s" % (self.rhx_gis, variables)
        if not "headers" in settings:
            settings["headers"] = dict()
        settings["headers"].update({
            # "X-IG-App-ID": "936619743392459",
            "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
        })

        return await self.get_request("https://www.instagram.com/graphql/query/", **settings)

    async def action_request(self, url, referer, data=None, settings=None):
        if not isinstance(referer, str):
            raise TypeError("'referer' must be str type")
        if not isinstance(url, str):
            raise TypeError("'url' must be str type")
        if not isinstance(data, dict) and not data is None:
            raise TypeError("'data' must be dict type or None")
        data = dict() if data is None else data.copy()
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        headers = {
            "Referer": referer,
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

        return await self.post_request(url, **settings)

    async def get_request(self, *args, **kwargs):
        try:
            return await self.session.get(*args, **kwargs)
        except aiohttp.ClientResponseError as exception:
            raise InternetException(exception)

    async def post_request(self, *args, **kwargs):
        try:
            return await self.session.post(*args, **kwargs)
        except aiohttp.ClientResponseError as exception:
            raise InternetException(exception)


class WebAgentAccount(Account, WebAgent):
    @exception_manager.decorator
    def __init__(self, username, cookies=None, logger=None):
        if not isinstance(username, str):
            raise TypeError("'username' must be str type")

        Account.__init__(self, username)
        WebAgent.__init__(self, cookies=cookies, logger=logger)

    @exception_manager.decorator
    def auth(self, password, settings=None):
        if not self.logger is None:
            self.logger.info("Auth started")
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        self.update(settings=settings)

        if not "headers" in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            # "X_Instagram-AJAX": "ee72defd9231",
            "X-CSRFToken": self.csrf_token,
            "Referer": "https://www.instagram.com/",
        })
        if not "data" in settings:
            settings["data"] = {}
        settings["data"].update({"username": self.username, "password": password})

        try:
            response = self.post_request(
                "https://www.instagram.com/accounts/login/ajax/",
                **settings,
            )
        except InternetException as exception:
            response = exception.response

        try:
            data = response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                checkpoint_url = "https://instagram.com" + data.get("checkpoint_url")
                data = self.checkpoint_handle(
                    url=checkpoint_url,
                    settings=settings,
                )
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=checkpoint_url,
                    navigation=data["navigation"],
                    types=data["types"],
                )
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Auth was unsuccessfully: %s", str(exception))
            raise UnexpectedResponse(exception, response.url)
        if not self.logger is None:
            self.logger.info("Auth was successfully")

    @exception_manager.decorator
    def checkpoint_handle(self, url, settings=None):
        if not self.logger is None:
            self.logger.info("Handle checkpoint page for '%s' started", self.username)
        response = self.get_request(url, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            data = data["entry_data"]["Challenge"][0]

            navigation = {
                key: "https://instagram.com" + value for key, value in data["navigation"].items()
            }

            data = data["extraData"]["content"]
            data = list(filter(lambda item: item["__typename"] == "GraphChallengePageForm", data))
            data = data[0]["fields"][0]["values"]
            types = []
            for d in data:
                types.append({"label": d["label"].lower().split(":")[0], "value": d["value"]})
            if not self.logger is None:
                self.logger.info("Handle checkpoint page for '%s' was successfull", self.username)
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Handle checkpoint page for '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint_send(self, checkpoint_url, forward_url, choice, settings=None):
        if not self.logger is None:
            self.logger.info("Send verify code for '%s' started", self.username)
        response = self.action_request(
            referer=checkpoint_url,
            url=forward_url,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = response.json()["navigation"]
            if not self.logger is None:
                self.logger.info("Send verify code for '%s' was successfully", self.username)
            return {
                key: "https://instagram.com" + value for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Send verify code by %s to '%s' was unsuccessfully: %s",
                    type,
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint_replay(self, forward_url, replay_url, settings=None):
        if not self.logger is None:
            self.logger.info("Resend verify code for '%s' started")
        response = self.action_request(
            url=replay_url,
            referer=forward_url,
            settings=settings,
        )
        try:
            navigation = response.json()["navigation"]
            if not self.logger is None:
                self.logger.info("Resend verify code for '%s' was successfull")
            return {
                key: "https://instagram.com" + value for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Resend verify code for '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint(self, url, code, settings=None):
        if not self.logger is None:
            self.logger.info("Verify account '%s' started")
        response = self.action_request(
            referer=url,
            url=url,
            data={"security_code": code},
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Verify account '%s' was successfull")
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Verify account '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return WebAgent.update(self, obj, settings=settings)

    @exception_manager.decorator
    def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return WebAgent.get_media(self, obj, pointer=pointer, count=count, limit=limit, delay=delay,
                               settings=settings)

    @exception_manager.decorator
    def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if account is None:
            account = self
        if not self.logger is None:
            self.logger.info("Get '%s' follows started", account)
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

        if account.id is None:
            self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    account.base_url,
                    getattr(account, account.primary_key),
                ), 
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
                    if not self.logger is None:
                        self.logger.info("Get '%s' follows was successfully", account)
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get '%s' follows was unsuccessfully: %s",
                        account,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0, settings=None):
        if account is None:
            account = self
        if not self.logger is None:
            self.logger.info("Get '%s' followers started", account)
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

        if account.id is None:
            self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    account.base_url,
                    getattr(account, account.primary_key),
                ),
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
                    if not self.logger is None:
                        self.logger.info("Get '%s' followers was successfully", account)
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get '%s' followers was unsuccessfully: %s",
                        account,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def stories(self, settings=None):
        if not self.logger is None:
            self.logger.info("Get stories started")
        response = self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer="https://instagram.com/%s%s" % (self.base_url, getattr(self, self.primary_key)),
            settings=settings,
        )

        try:
            data = response.json()["data"]["user"]["feed_reels_tray"]["edge_reels_tray_to_reel"]
            if not self.logger is None:
                self.logger.info("Get stories was successfully")
            return [Story(edge["node"]["id"]) for edge in data["edges"]]
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Get stories was unsuccessfully: %s", str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not self.logger is None:
            self.logger.info("Get feed started")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

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
                referer="https://instagram.com/%s%s" % (
                    self.base_url,
                    getattr(self, self.primary_key),
                ),
                settings=settings,
            )

            try:
                data = response.json()["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if not "shortcode" in node:
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
                    if not self.logger is None:
                        self.logger.info("Get feed was successfully")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get feed was unsuccessfully: %s", str(exception))
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def like(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Like '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/like/" % media.id,
            settings=settings,
        )

        try:
            if not self.logger is None:
                self.logger.info("Like '%s' was successfully", media)
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Like '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unlike(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Unlike '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Like '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def save(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Save '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/save/" % media.id,
            settings=settings,
        )

        try:
            if not self.logger is None:
                self.logger.info("Save '%s' was successfully", media)
            return response.json()["status"] == "ok"
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Save '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unsave(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Unsave '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/unsave/" % media.id,
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Unsave '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Unsave '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def add_comment(self, media, text, settings=None):
        if not self.logger is None:
            self.logger.info("Comment '%s' started")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        if media.id is None:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/comments/%s/add/" % media.id,
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
            if not self.logger is None:
                self.logger.info("Comment '%s' was successfully", media)
            return comment
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Comment '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def delete_comment(self, comment, settings=None):
        if not self.logger is None:
            self.logger.info("Delete comment '%s' started", comment)
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        if comment.media.id is None:
            self.update(comment.media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % comment.media.code,
            url="https://www.instagram.com/web/comments/%s/delete/%s/" % (
                comment.media.id,
                comment.id,
            ),
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if result:
                del comment
            if not self.logger is None:
                self.logger.info("Delete comment '%s' was successfully", comment)
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Delete comment '%s' was unsuccessfully: %s",
                    comment,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def follow(self, account, settings=None):
        if not self.logger is None:
            self.logger.info("Follow to '%s' started", account)
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/follow/" % account.id,
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Follow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Follow to '%s' was unsuccessfully: %s", account, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unfollow(self, account, settings=None):
        if not self.logger is None:
            self.logger.info("Unfollow to '%s' started", account)
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/unfollow/" % account.id,
            settings=settings,
        )

        try:
            result = response.json()["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Unfollow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Unfollow to '%s' was unsuccessfully: %s",
                    account,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)


class AsyncWebAgentAccount(Account, AsyncWebAgent):
    def __init__(self, username, cookies=None, logger=None):
        if not isinstance(username, str):
            raise TypeError("'username' must be str type")

        Account.__init__(self, username)
        AsyncWebAgent.__init__(self, cookies=cookies, logger=logger)

    def __del__(self):
        Account.__del__(self)

    async def delete(self):    
        await self.session.close()

    async def auth(self, password, settings=None):
        if not self.logger is None:
            self.logger.info("Auth started")
        if not isinstance(password, str):
            raise TypeError("'password' must be str type")
        if not isinstance(settings, dict) and not settings is None:
            raise TypeError("'settings' must be dict type or None")
        settings = dict() if settings is None else settings.copy()

        await self.update(settings=settings)

        if not "headers" in settings:
            settings["headers"] = {}
        settings["headers"].update({
            "X-IG-App-ID": "936619743392459",
            # "X_Instagram-AJAX": "ee72defd9231",
            "X-CSRFToken": self.csrf_token,
            "Referer": "https://www.instagram.com/",
        })
        if not "data" in settings:
            settings["data"] = {}
        settings["data"].update({"username": self.username, "password": password})

        response = await self.post_request(
            "https://www.instagram.com/accounts/login/ajax/",
            **settings,
        )

        try:
            data = await response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                checkpoint_url = "https://instagram.com" + data.get("checkpoint_url")
                data = await self.checkpoint_handle(
                    url=checkpoint_url,
                    settings=settings,
                )
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=checkpoint_url,
                    navigation=data["navigation"],
                    types=data["types"],
                )
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Auth was unsuccessfully: %s", str(exception))
            raise UnexpectedResponse(exception, response.url)
        if not self.logger is None:
            self.logger.info("Auth was successfully")       

    @exception_manager.decorator
    async def checkpoint_handle(self, url, settings=None):
        if not self.logger is None:
            self.logger.info("Handle checkpoint page for '%s' started", self.username)
        response = await self.get_request(url, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                await response.text(),
            )
            data = json.loads(match.group(1))
            data = data["entry_data"]["Challenge"][0]

            navigation = {
                key: "https://instagram.com" + value for key, value in data["navigation"].items()
            }

            data = data["extraData"]["content"]
            data = list(filter(lambda item: item["__typename"] == "GraphChallengePageForm", data))
            data = data[0]["fields"][0]["values"]
            types = []
            for d in data:
                types.append({"label": d["label"].lower().split(":")[0], "value": d["value"]})
            if not self.logger is None:
                self.logger.info("Handle checkpoint page for '%s' was successfull", self.username)
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Handle checkpoint page for '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def checkpoint_send(self, checkpoint_url, forward_url, choice, settings=None):
        if not self.logger is None:
            self.logger.info("Send verify code for '%s' started", self.username)
        response = await self.action_request(
            referer=checkpoint_url,
            url=forward_url,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = (await response.json())["navigation"]
            if not self.logger is None:
                self.logger.info("Send verify code for '%s' was successfully", self.username)
            return {
                key: "https://instagram.com" + value for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Send verify code by %s to '%s' was unsuccessfully: %s",
                    type,
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def checkpoint_replay(self, forward_url, replay_url, settings=None):
        if not self.logger is None:
            self.logger.info("Resend verify code for '%s' started")
        response = await self.action_request(
            url=replay_url,
            referer=forward_url,
            settings=settings,
        )
        try:
            navigation = (await response.json())["navigation"]
            if not self.logger is None:
                self.logger.info("Resend verify code for '%s' was successfull")
            return {
                key: "https://instagram.com" + value for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Resend verify code for '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def checkpoint(self, url, code, settings=None):
        if not self.logger is None:
            self.logger.info("Verify account '%s' started")
        response = await self.action_request(
            referer=url,
            url=url,
            data={"security_code": code},
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Verify account '%s' was successfull", self.username)
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Verify account '%s' was unsuccessfull: %s",
                    self.username,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def update(self, obj=None, settings=None):
        if obj is None:
            obj = self
        return await AsyncWebAgent.update(self, obj, settings=settings)

    @exception_manager.decorator
    async def get_media(self, obj=None, pointer=None, count=12, limit=12, delay=0, settings=None):
        if obj is None:
            obj = self
        return await AsyncWebAgent.get_media(self, obj, pointer=pointer, count=count, limit=limit,
                                          delay=delay, settings=settings)

    @exception_manager.decorator
    async def get_follows(self, account=None, pointer=None, count=20, limit=50, delay=0,
                          settings=None):
        if account is None:
            account = self
        if not self.logger is None:
            self.logger.info("Get '%s' follows started", account)
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

        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="58712303d941c6855d4e888c5f0cd22f",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    account.base_url,
                    getattr(account, account.primary_key),
                ),
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
                    if not self.logger is None:
                        self.logger.info("Get '%s' follows was successfully", account)
                    return follows, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get '%s' follows was unsuccessfully: %s",
                        account,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def get_followers(self, account=None, pointer=None, count=20, limit=50, delay=0,
                            settings=None):
        if account is None:
            account = self
        if not self.logger is None:
            self.logger.info("Get '%s' followers started", account)
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

        if account.id is None:
            await self.update(account, settings=settings)

        if pointer is None:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        while True:
            data = {"first": min(limit, count), "id": account.id}
            if not pointer is None:
                data["after"] = pointer

            response = await self.graphql_request(
                query_hash="37479f2b8209594dde7facb0d904896a",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s" % (
                    account.base_url,
                    getattr(account, account.primary_key),
                ),
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
                    if not self.logger is None:
                        self.logger.info("Get '%s' followers was successfully", account)
                    return followers, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error(
                        "Get '%s' followers was unsuccessfully: %s",
                        account,
                        str(exception),
                    )
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def stories(self, settings=None):
        if not self.logger is None:
            self.logger.info("Get stories started")
        response = await self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer="https://instagram.com/%s%s" % (self.base_url, getattr(self, self.primary_key)),
            settings=settings,
        )

        try:
            data = (await response.json())["data"]["user"]["feed_reels_tray"]
            data = data["edge_reels_tray_to_reel"]
            result = [Story(edge["node"]["id"]) for edge in data["edges"]]
            if not self.logger is None:
                self.logger.info("Get stories was successfully")
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Get stories was unsuccessfully: %s", str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def feed(self, pointer=None, count=12, limit=50, delay=0, settings=None):
        if not self.logger is None:
            self.logger.info("Get feed started")
        if not isinstance(pointer, str) and not pointer is None:
            raise TypeError("'pointer' must be str type or None")
        if not isinstance(count, int):
            raise TypeError("'count' must be int type")
        if not isinstance(limit, int):
            raise TypeError("'limit' must be int type")
        if not isinstance(delay, (int, float)):
            raise TypeError("'delay' must be int or float type")

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
                referer="https://instagram.com/%s%s" % (
                    self.base_url,
                    getattr(self, self.post_request),
                ),
                settings=settings,
            )

            try:
                data = (await response.json())["data"]["user"]["edge_web_feed_timeline"]
                edges = data["edges"]
                page_info = data["page_info"]
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index]["node"]
                    if not "shortcode" in node:
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
                    if not self.logger is None:
                        self.logger.info("Get feed was successfully")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                if not self.logger is None:
                    self.logger.error("Get feed was unsuccessfully: %s", str(exception))
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def like(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Like '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        
        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/like/" % media.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Like '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def unlike(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Unlike '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Like '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Like '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def save(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Save '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/save/" % media.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Save '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Save '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def unsave(self, media, settings=None):
        if not self.logger is None:
            self.logger.info("Unsave '%s' started", media)
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/unsave/" % media.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Unsave '%s' was successfully", media)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Unsave '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def add_comment(self, media, text, settings=None):
        if not self.logger is None:
            self.logger.info("Comment '%s' started")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")
        if not isinstance(text, str):
            raise TypeError("'text' must be str type")

        if media.id is None:
            await self.update(media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/comments/%s/add/" % media.id,
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
            if not self.logger is None:
                self.logger.info("Comment '%s' was successfully", media)
            return comment
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Comment '%s' was unsuccessfully: %s", media, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def delete_comment(self, comment, settings=None):
        if not self.logger is None:
            self.logger.info("Delete comment '%s' started", comment)
        if not isinstance(comment, Comment):
            raise TypeError("'comment' must be Comment type")

        if comment.media.id is None:
            await self.update(comment.media, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/p/%s/" % comment.media.code,
            url="https://www.instagram.com/web/comments/%s/delete/%s/" % (
                comment.media.id,
                comment.id,
            ),
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if result:
                del comment
            if not self.logger is None:
                self.logger.info("Delete comment '%s' was successfully", comment)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Delete comment '%s' was unsuccessfully: %s",
                    comment,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def follow(self, account, settings=None):
        if not self.logger is None:
            self.logger.info("Follow to '%s' started", account)
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/follow/" % account.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Follow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error("Follow to '%s' was unsuccessfully: %s", account, str(exception))
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    async def unfollow(self, account, settings=None):
        if not self.logger is None:
            self.logger.info("Unfollow to '%s' started", account)
        if not isinstance(account, Account):
            raise TypeError("'account' must be Account type")

        if account.id is None:
            await self.update(account, settings=settings)

        response = await self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/unfollow/" % account.id,
            settings=settings,
        )

        try:
            result = (await response.json())["status"] == "ok"
            if not self.logger is None:
                self.logger.info("Unfollow to '%s' was successfully", account)
            return result
        except (ValueError, KeyError) as exception:
            if not self.logger is None:
                self.logger.error(
                    "Unfollow to '%s' was unsuccessfully: %s",
                    account,
                    str(exception),
                )
            raise UnexpectedResponse(exception, response.url)
