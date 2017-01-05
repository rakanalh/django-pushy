class PushException(Exception):
    pass


class PushAuthException(PushException):
    pass


class PushInvalidTokenException(PushException):
    pass


class PushInvalidDataException(PushException):
    pass


class PushServerException(PushException):
    pass
