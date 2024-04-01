from minerva.core.service.exceptions import ServiceError


class InvalidAccessTokenError(ServiceError): ...


class ExpiredAccessTokenError(ServiceError): ...
