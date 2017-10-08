#!/usr/bin/python3

import requests
from requests.exceptions import *
from time import sleep	
	
# Exception classes
class InstagramException(Exception):
	pass

class InternetException(InstagramException):
	def __init__(self, e):
		self.error=e
	
	def __getattr__(self, name):
		return self.error.__getattribute__(name)
	
	def __str__(self):
		return "Error by connection with Instagram to '{0}' with response code '{1}'".format(self.error.request.url, self.error.response.status_code)
	
class AuthException(Exception):
	def __init__(self, login):
		super().__init__("Cannot auth user with username '{0}'".format(login))

class UnexpectedResponse(InstagramException):
	def __init__(self, url, data=None):
		super().__init__("Get unexpected response from '{0}' with data: {1}".format(url, str(data)))

class NotUpdatedElement(InstagramException):
	def __init__(self, element):
		super().__init__("Cannot use not updated {0} {1}".format(element.__class__.__name__, element))

# Exception struct
class ExceptionTree:
	def __init__(self):
		self.__tree__={
			'action': lambda exception, *args, **kwargs: (args, kwargs),
			'branch': {},
		}
	
	def __getitem__(self, key):
		# Check data
		if not issubclass(key, Exception):
			raise TypeError("Key must be Exception type")
		return self.__search__(key)['action']
	
	def __setitem__(self, key, value):
		# Check data
		if not issubclass(key, Exception):
			raise TypeError("Key must be Exception type")
		if not callable(value):
			raise TypeError("Value must be function")
		
		item, exists=self.__search__(key, False)
		if exists:
			item['action']=value
		else:
			item['branch'][key]={'branch': {}, 'action': value}
	
	def __search__(self, exception, get=True):
		# Check data
		if not issubclass(exception, Exception):
			raise TypeError("'exception' must be Exception type")
		
		# Search
		current=self.__tree__
		while True:
			for key, value in current['branch'].items():
				if key==exception:
					if not get:
						return value, True
					return value
				elif issubclass(exception, key):
					current=value
					break
			else:
				if not get:
					return current, False
				return current
			continue

# Cache class for optimized memory
class ElementConstructor(type):
	def __new__(cls, name, classes, fields):
		fields["__del__"]=ElementConstructor.__custom_del__
		fields["__str__"]=lambda self: str(self.__getattribute__(self.__primarykey__))
		fields["__repr__"]=lambda self: str(self.__getattribute__(self.__primarykey__))
		fields["__updated__"]=False
		return type.__new__(cls, name, classes, fields)
	
	def __custom_del__(self):
		del self.__cache__[self.__getattribute__(self.__primarykey__)]
	
	def __call__(cls, key, *args, **kwargs):
		if not key in cls.__cache__:
			cls.__cache__[key]=super().__call__(key, *args, **kwargs)
		return cls.__cache__[key]

class Agent:
	# Anonymous session
	__session__=requests
	repeats=1
	
	def exceptionDecorator(func):
		def wrapper(*args, **kwargs):
			count=0
			while True:
				count+=1
				try:
					return func(*args, **kwargs)
				except Exception as e:
					if count<Agent.repeats:
						args, kwargs=self.exception_actions[e.__class__](e, *args, **kwargs)
					else:
						raise e
		return wrapper
	
	def __http_error_action__(exception, *args, **kwargs):
		if exception.status_code in (403, 429):
			sleep(2)
			return (args, kwargs)
		raise exception
	
	exception_actions=ExceptionTree()
	exception_actions[HTTPError]=__http_error_action__
	
	@exceptionDecorator
	def update(self, obj, settings={}):
		# Checks and set data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if isinstance(obj, Account):
			query="https://www.instagram.com/{0}/?__a=1".format(obj.login)
		elif isinstance(obj, Media):
			query="https://www.instagram.com/p/{0}?__a=1".format(obj.code)
		elif isinstance(obj, Location):
			query="https://www.instagram.com/explore/locations/{0}/?__a=1".format(obj.id)
		elif isinstance(obj, Tag):
			query="https://www.instagram.com/explore/tags/{0}/?__a=1".format(obj.name)
		else:
			raise TypeError("obj must be Account, Media, Location or Tag")
		
		# Request
		response=self.__send_get_request__(query, **settings)
		
		# Parsing info
		try:
			obj.__setDataFromJSON__(response.json())
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)			
		obj.__updated__=True
	
	@exceptionDecorator
	def getMedia(self, obj, count=12, settings={}):
		# Checks data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if isinstance(obj, Account):
			data={'query_id': 17888483320059182, 'variables': '{"id": '+str(obj.id)+', "first": '+str(count)+'}'}
		elif isinstance(obj, Location):
			data={'query_id': 17865274345132052, 'variables': '{"id": '+str(obj.id)+', "first": '+str(count)+'}'}
		elif isinstance(obj, Tag):
			data={'query_id': 17875800862117404, 'variables': '{"tag_name": "'+obj.name+'", "first": '+str(count)+'}'}
		else:
			raise TypeError("'obj' must be Account type")
		if not obj.__updated__:
			raise NotUpdatedElement(account)
		
		# Set data
		if 'params' in settings:
			settings['params'].update(data)
		else:
			settings['params']=data
		media_set=set()
		stop=False
		
		while not stop:
			# Send request
			response=self.__send_get_request__(
				"https://www.instagram.com/graphql/query/",
				**settings,
			)
			
			# Parsing info
			try:
				if isinstance(obj, Account):
					data=response.json()['data']['user']['edge_owner_to_timeline_media']
				elif isinstance(obj, Location):
					data=response.json()['data']['location']['edge_location_to_media']
				elif isinstance(obj, Tag):
					data=response.json()['data']['hashtag']['edge_hashtag_to_media']
				for media in data['edges']:
					m=Media(media['node']['shortcode'])
					obj.media.add(m)
					media_set.add(m)
				if len(data['edges'])<count and data['page_info']['has_next_page']:
					count=count-len(data['edges'])
					if isinstance(obj, Tag):
						settings['params']['variables']='{"tag_name": "'+obj.name+'", "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
					else:
						settings['params']['variables']='{"id": '+str(obj.id)+', "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
				else:
					stop=True
			except (ValueError, KeyError):
				raise UnexpectedResponse(response.url, response.text)
		return media_set
	
	@exceptionDecorator
	def getLikes(self, media, count=20,	settings={}):
		# Check data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(media, Media):
			raise TypeError("'media' must be Media type")
		if not media.__updated__:
			raise NotUpdatedElement(media)
		
		# Set data
		data={'query_id': 17864450716183058, "variables": '{"shortcode": "'+media.code+'", "first": '+str(count)+'}'}
		if 'params' in settings:
			settings['params'].update(data)
		else:
			settings['params']=data
		likes_set=set()
		stop=False
		
		while not stop:
			# Request for get info
			response=self.__send_get_request__(
				"https://www.instagram.com/graphql/query/",
				**settings,
			)
		
			# Parsing info
			try:
				data=response.json()['data']['shortcode_media']['edge_liked_by']
				media.likes_count=data['count']
				for edge in data['edges']:
					account=Account(edge['node']['username'])
					media.likes.add(account)
					likes_set.add(account)
				if len(data['edges'])<count and data['page_info']['has_next_page']:
					count=count-len(data['edges'])
					settings['params']['variables']='{"shortcode": "'+media.code+'", "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
				else:
					stop=True
			except (ValueError, KeyError):
				raise UnexpectedResponse(response.url, response.text)
		return likes_set
	
	@exceptionDecorator
	def getComments(self, media, count=20, settings={}):
		# Check data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(media, Media):
			raise TypeError("'media' must be Media type")
		if not media.__updated__:
			raise NotUpdatedElement(media)
		
		# Set data
		data={'query_id': 17852405266163336, 'variables': '{"shortcode": "'+media.code+'", "first": '+str(count)+'}'}
		if 'params' in settings:
			settings['params'].update(data)
		else:
			settings['params']=data
		comments_set=set()
		stop=False
		
		while not stop:
			# Request for get info
			response=self.__send_get_request__(
				"https://www.instagram.com/graphql/query/",
				**settings,
			)
		
			# Parsing info
			try:
				data=response.json()['data']['shortcode_media']['edge_media_to_comment']
				media.comments_count=data['count']
				for edge in data['edges']:
					comment=Comment(
						id=edge['node']['id'],
						media=media,
						owner=Account(edge['node']['owner']['username']),
						text=edge['node']['text'],
						data=edge['node']['created_at'],
					)
					media.comments.add(comment)
					comments_set.add(comment)
				if len(data['edges'])<count and data['page_info']['has_next_page']:
					count=count-len(data['edges'])
					settings['params']['variables']='{"shortcode": "'+media.code+'", "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
				else:
					stop=True
			except (ValueError, KeyError):
				raise UnexpectedResponse(response.url, response.text)
		return comments_set

	def __send_get_request__(self, *args, **kwargs):
		count=0
		while True:
			count+=1
			try:
				response=self.__session__.get(*args, **kwargs)
				response.raise_for_status()
				return response
			except Exception as e:
				if count<self.repeats:
					args, kwargs=self.exception_actions[e.__class__](e, *args, **kwargs)
				else:
					raise InternetException(e)
	
	def __send_post_request__(self, *args, **kwargs):
		count=0
		while True:
			count+=1
			try:
				response=self.__session__.post(*args, **kwargs)
				response.raise_for_status()
				return response
			except Exception as e:
				if count<self.repeats:
					args, kwargs=self.exception_actions[e.__class__](e, *args, **kwargs)
				else:
					raise InternetException(e)
	
# Account class
class Account(metaclass=ElementConstructor):
	__cache__=dict()
	__primarykey__="login"
	
	def __init__(self, login):
		self.id=None
		self.login=login
		self.full_name=None
		self.profile_pic_url=None
		self.profile_pic_url_hd=None
		self.fb_page=None
		self.biography=None
		self.follows_count=None
		self.followers_count=None
		self.media_count=None
		self.is_private=None
		self.is_verified=None
		self.has_blocked_viewer=None
		self.blocked_by_viewer=None
		self.has_requested_viewer=None
		self.requested_by_viewer=None
		self.country_block=None
		# Lists
		self.media=set()
		self.follows=set()
		self.followers=set()

	def __setDataFromJSON__(self, data):
		data=data['user']
		self.id=data['id']
		self.full_name=data['full_name']
		self.profile_pic_url=data['profile_pic_url']
		self.profile_pic_url_hd=data['profile_pic_url_hd']
		self.fb_page=data['connected_fb_page']
		self.biography=data['biography']
		self.follows_count=data['follows']['count']
		self.followers_count=data['followed_by']['count']
		self.media_count=data['media']['count']
		self.is_private=data['is_private']
		self.is_verified=data['is_verified']
		self.has_blocked_viewer=data['has_blocked_viewer']
		self.blocked_by_viewer=data['blocked_by_viewer']
		self.has_requested_viewer=data['has_requested_viewer']
		self.requested_by_viewer=data['requested_by_viewer']
		self.country_block=data['country_block']

class AgentAccount(Account, Agent):
	# Session for user
	__session__=requests.Session()
	
	@Agent.exceptionDecorator
	def __init__(self, login, password, settings={}):
		super().__init__(login)
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		# Request for get start page for get CSRFToken
		response=self.__send_get_request__(
			"https://www.instagram.com/",
			**settings
		)
		# Create login data structure
		data={
			"username": self.login,
			"password": password,
		}
		# Create headers
		headers={
			"X-CSRFToken": response.cookies["csrftoken"],
			"referer": "https://www.instagram.com/",
		}
		# Login request
		response=self.__send_post_request__(
			"https://www.instagram.com/accounts/login/ajax/",
			data=data,
			headers=headers,
			**settings,
		)
		
		# Parse response info
		try:
			data=response.json()
			if not data['authenticated']:
				raise AuthException(self.login) 
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)
	
	def update(self, obj=None, settings={}):
		if not obj:
			obj=self
		return super().update(obj, settings)
	
	def getMedia(self, obj=None, count=12, settings={}):
		if not obj:
			obj=self
		return super().getMedia(obj, count,	settings)
	
	@Agent.exceptionDecorator
	def getFollows(self, account=None, count=20, settings={}):
		# Check set and data
		if not account:
			account=self
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(account, Account):
			raise TypeError("'account' must be Account type")
		if not account.__updated__:
			raise NotUpdatedElement(account)
			
		# Set data
		data={"query_id": 17874545323001329, 'variables': '{"id": '+str(account.id)+', "first": '+str(count)+'}'}
		if 'params' in settings:
			settings['params'].update(data)
		else:
			settings['params']=data
		follows_set=set()
		stop=False
		
		while not stop:
			# Request for get info
			response=self.__send_get_request__(
				"https://www.instagram.com/graphql/query/",
				**settings,
			)
		
			# Parsing info
			try:
				data=response.json()['data']['user']['edge_follow']
				account.follows_count=data['count']
				for edge in data['edges']:
					a=Account(edge['node']['username'])
					account.follows.add(a)
					follows_set.add(a)
				# Recursive calling method if not all elements was loading
				if len(data['edges'])<count and data['page_info']['has_next_page']:
					count=count-len(data['edges'])
					settings['params']['variables']='{"id": '+str(account.id)+', "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
				else:
					stop=True
			except (ValueError, KeyError):
				raise UnexpectedResponse(response.url, response.text)
		return follows_set
	
	@Agent.exceptionDecorator
	def getFollowers(self, account=None, count=20, settings={}):
		# Check data
		if not account:
			account=self
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(account, Account):
			raise TypeError("'account' must be Account type")
		if not account.__updated__:
			raise NotUpdatedElement(account)
		
		# Set data
		data={'query_id': 17851374694183129, 'variables': '{"id": '+str(account.id)+', "first": '+str(count)+'}'}
		if 'params' in settings:
			settings['params'].update(data)
		else:
			settings['params']=data
		followers_set=set()
		stop=False
		
		while not stop:
			# Request for get info
			response=self.__send_get_request__(
				"https://www.instagram.com/graphql/query/",
				**settings,
			)
		
			# Parsing info
			try:
				data=response.json()['data']['user']['edge_followed_by']
				account.followers_count=data['count']
				for edge in data['edges']:
					a=Account(edge['node']['username'])
					account.followers.add(a)
					followers_set.add(a)
				# Recursive calling method if not all elements was loading
				if len(data['edges'])<count and data['page_info']['has_next_page']:
					count=count-len(data['edges'])
					settings['params']['variables']='{"id": '+str(account.id)+', "first": '+str(count)+', "after": "'+data['page_info']['end_cursor']+'"}'
				else:
					stop=True
			except (ValueError, KeyError):
				raise UnexpectedResponse(response.url, response.text)
		return followers_set
	
	@Agent.exceptionDecorator
	def like(self, media, settings={}):
		# Check data
		if not isinstance(media, Media):
			raise TypeError("'media' must be Media type")
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not media.__updated__:
			raise NotUpdatedElement(media)
		
		response=self.__action_handler__(
			referer="https://www.instagram.com/p/{0}/?taken-by={1}".format(media.code, media.owner.login),
			url="https://www.instagram.com/web/likes/{0}/like/".format(media.id),
		)
		
		# Parsing
		try:
			if response.json()['status']=='ok':
				return True
			else:
				return False
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)
	
	@Agent.exceptionDecorator	
	def unlike(self, media, settings={}):
		# Check data
		if not isinstance(media, Media):
			raise TypeError("'media' must be Media type")
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not media.__updated__:
			raise NotUpdatedElement(media)
		
		# Request
		response=self.__action_handler__(
			referer="https://www.instagram.com/p/{0}/?taken-by={1}".format(media.code, media.owner.login),
			url="https://www.instagram.com/web/likes/{0}/unlike/".format(media.id),
		)
		
		# Parsing
		try:
			if response.json()['status']=='ok':
				return True
			else:
				return False
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)
	
	@Agent.exceptionDecorator
	def addComment(self, media, text, settings={}):
		# Check data
		if not isinstance(media, Media):
			raise TypeError("'media' must be Media type")
		if not isinstance(text, str):
			raise TypeError("'text' must be str type")
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not media.__updated__:
			raise NotUpdatedElement(media)
		
		# Send request
		response=self.__action_handler__(
			referer="https://www.instagram.com/p/{0}/?taken-by={1}".format(media.code, media.owner.login),
			url="https://www.instagram.com/web/comments/{0}/add/".format(media.id),
			data={'comment_text': text},
		)
		
		# Parsing
		try:
			data=response.json()
			if data['status']=='ok':
				comment=Comment(
					id=data['id'],
					media=media,
					owner=self,
					text=data['text'],
					data=data['created_time'],
				)
				return comment
			return None
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)

	@Agent.exceptionDecorator
	def deleteComment(self, comment, settings={}):
		# Check data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(comment, Comment):
			raise TypeError("'comment' must be Comment type")
		if not comment.__updated__:
			raise NotUpdatedElement(comment)
		if not comment.media.__updated__:
			raise NotUpdatedElement(comment.media)
		
		# Send request
		response=self.__action_handler__(
			referer="https://www.instagram.com/p/{0}/?taken-by={1}".format(comment.media.code, comment.media.owner.login),
			url="https://www.instagram.com/web/comments/{0}/delete/{1}/".format(comment.media.id, comment.id),
		)
		
		print(response.status_code)
		# Parsing
		try:
			if response.json()['status']=='ok':
				del comment
				return True
			else:
				return False
		except (ValueError, KeyError):
			raise UnexpectedResponse(response.url, response.text)

	def __action_handler__(self, referer, url, data={}, settings={}):
		# Check data
		if not isinstance(settings, dict):
			raise TypeError("'settings' must be dict type")
		if not isinstance(data, dict):
			raise TypeError("'data' must be dict type")
		if not isinstance(referer, str):
			raise TypeError("'referer' must be str type")
		if not isinstance(url, str):
			raise TypeError("'url' must be str type")
		
		# Set data
		headers={
			'referer': referer,
			'x-csrftoken': self.__session__.cookies['csrftoken'],
			'x-instagram-ajax': '1',
			'x-requested-with': 'XMLHttpRequest',
		}
		if 'headers' in settings:
			settings['headers'].update(headers)
		else:
			settings['headers']=headers
		if 'data' in settings:
			settings['data'].update(data)
		else:
			settings['data']=data
		
		# Send request
		response=self.__session__.post(url, **settings)
		return response
	
class Media(metaclass=ElementConstructor):
	__cache__={}
	__primarykey__="code"
	
	def __init__(self, code):
		self.id=None
		self.code=code
		self.caption=None
		self.owner=None
		self.date=None
		self.location=None
		self.likes_count=None
		self.comments_count=None
		self.comments_disabled=None
		self.is_video=None
		self.is_ad=None
		# Lists
		self.likes=set()
		self.comments=set()

	def __setDataFromJSON__(self, data):
		data=data['graphql']['shortcode_media']
		self.id=data['id']
		self.code=data['shortcode']
		if data['edge_media_to_caption']['edges']:
			self.caption=data['edge_media_to_caption']['edges'][0]['node']['text']
		else:
			self.caption=None
		self.owner=Account(data['owner']['username'])
		self.date=data['taken_at_timestamp']
		if data['location']:
			self.location=Location(data['location']['id'])
		self.likes_count=data['edge_media_preview_like']['count']
		self.comments_count=data['edge_media_to_comment']['count']
		self.comments_disabled=data['comments_disabled']
		self.is_video=data['is_video']
		self.is_ad=data['is_ad']

class Location(metaclass=ElementConstructor):
	__cache__={}
	__primarykey__="id"
	
	def __init__(self, id):
		self.id=int(id)
		self.slug=None
		self.name=None
		self.has_public_page=None
		self.directory=None
		self.coordinates=None
		self.media_count=None
		# Lists
		self.media=set()
		self.top_posts=set()
	
	def __setDataFromJSON__(self, data):
		data=data['location']
		self.id=data['id']
		self.slug=data['slug']
		self.name=data['name']
		self.has_public_page=data['has_public_page']
		if 'directory' in data:
			self.directory=data['directory']
		self.coordinates=(data['lat'], data['lng'])
		self.media_count=data['media']['count']
		for node in data['top_posts']['nodes']:
			self.top_posts.add(Media(node['code']))

class Tag(metaclass=ElementConstructor):
	__cache__={}
	__primarykey__="name"
	
	def __init__(self, name):
		self.name=name
		self.media_count=None
		# Lists
		self.media=set()
		self.top_posts=set()
	
	def __setDataFromJSON__(self, data):
		data=data['tag']
		self.name=data['name']
		self.media_count=data['media']['count']
		for node in data['top_posts']['nodes']:
			self.top_posts.add(Media(node['code']))

class Comment(metaclass=ElementConstructor):
	__cache__={}
	__primarykey__="id"
	
	def __init__(self, id, media, owner, text, data):
		self.id=int(id)
		self.media=media
		self.owner=owner
		self.text=text
		self.data=data
		self.__updated__=True

