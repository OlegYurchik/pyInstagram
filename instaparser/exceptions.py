from time import sleep



# Exceptions
class InstagramException(Exception):
    pass


class InternetException(InstagramException):
    def __init__(self, exception):
        super().__init__("Error by connection with Instagram to '%s' with response code '%s'" % (exception.request.url, exception.response.status_code))

        self.request = exception.request
        self.response = exception.response


class AuthException(InstagramException):
    def __init__(self, login):
        super().__init__("Cannot auth user with username '%s'" % login)


class UnexpectedResponse(InstagramException):
    def __init__(self, url, data=None):
        super().__init__("Get unexpected response from '%s' with data: %s" % (url, str(data)))


class NotUpdatedElement(InstagramException):
    def __init__(self, element, argument):
        super().__init__("Element '%s' haven't argument %s. Please, update this element" % (element.__repr__(), argument))



# Exception handlers
def http_response_handler(exception, *args, **kwargs):
    if exception.response.status_code == 429:
        sleep(600)
        return (args, kwargs)
    if exception.response.status_code == 400:
        sleep(60)
        pass

    raise exception



# Exception manager
class ExceptionManager:
    def __init__(self):
        self._tree = {
            'action': lambda exception, *args, **kwargs: (args, kwargs),
            'branch': {},
        }
        self.repeats=1


    def __getitem__(self, key):
        # Check data
        if not issubclass(key, Exception):
            raise TypeError("Key must be Exception type")

        return self._search(key)[0]['action']


    def _search(self, exception):
        # Check data
        if not issubclass(exception, Exception):
            raise TypeError("'exception' must be Exception type")

        # Search
        current = self._tree
        while True:
            for key, value in current['branch'].items():
                if key == exception:
                    return value, True
                elif issubclass(exception, key):
                    current = value
                    break
            else:
                return current, False
            continue


    def __setitem__(self, key, value):
        # Check data
        if not issubclass(key, Exception):
            raise TypeError("Key must be Exception type")
        if not callable(value):
            raise TypeError("Value must be function")

        item, exists = self._search(key)
        if exists:
            item['action'] = value
        else:
            item['branch'][key] = {'branch': {}, 'action': value}


    def decorator(manager, func):
        def wrapper(self, *args, **kwargs):
            for count in range(manager.repeats):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    exception = e
                    args, kwargs = manager[exception.__class__](exception, *args, **kwargs)
            else:
                raise exception

        return wrapper
