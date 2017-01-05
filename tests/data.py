from pushjack import (
    GCMCanonicalID
)


class ResponseMock:
    def __init__(self, status_code):
        self.status_code = status_code
        self.errors = []
        self.canonical_ids = []


def valid_response():
    return ResponseMock(200)


def valid_with_canonical_id_response(canonical_id):
    canonical_id_obj = GCMCanonicalID(canonical_id, canonical_id)
    response = ResponseMock(200)
    response.canonical_ids = [canonical_id_obj]
    return response


def invalid_with_exception(exc):
    response = ResponseMock(400)
    response.errors.append(exc)
    return response
