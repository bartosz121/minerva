from minerva.access_token.models import AccessToken
from minerva.core.repository.sqlalchemy import SQLAlchemyRepository


class AccessTokenRepository(SQLAlchemyRepository[AccessToken, str]):
    model = AccessToken
    model_id_attr_name = "token"
