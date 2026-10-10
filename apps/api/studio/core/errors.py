"""Domain errors mapped to HTTP responses by the API layer."""


class StudioError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(StudioError):
    status_code = 404
    code = "not_found"


class ConflictError(StudioError):
    status_code = 409
    code = "conflict"


class ValidationFailed(StudioError):
    status_code = 422
    code = "validation_failed"


class PayloadTooLarge(StudioError):
    status_code = 413
    code = "payload_too_large"
