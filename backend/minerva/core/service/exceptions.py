class ServiceError(Exception):
    """Base exception for service errors"""


class NotFoundError(ServiceError): ...
