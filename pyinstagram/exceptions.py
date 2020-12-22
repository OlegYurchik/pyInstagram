from aiohttp import ClientResponseError


class InstagramException(Exception):
    pass


class AuthException(InstagramException):
    def __init__(self, username, message=""):
        super().__init__("Cannot auth user with username '%s': %s" % (username, message))


class CheckpointException(AuthException):
    def __init__(self, username, checkpoint_url, navigation, types):
        super().__init__(username, "need verification by checkpoint")
        self.checkpoint_url = checkpoint_url
        self.navigation = navigation
        self.types = types


class IncorrectVerificationTypeException(AuthException):
    def __init__(self, username, type):
        super().__init__(username, "incorrect verification type '%s'" % type)
        self.type = type


class NotUpdatedElement(InstagramException):
    def __init__(self, element, argument):
        super().__init__("Element '%s' haven't argument %s. Please, update this element" % (
            element.__repr__(),
            argument,
        ))
