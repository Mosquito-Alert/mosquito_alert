from rest_framework_simplejwt.tokens import Token as OriginalToken, SlidingToken as OriginalSlidingToken, RefreshToken as OriginalRefreshToken

from tigaserver_app.models import TigaUser


class Token(OriginalToken):
    USER_TYPE_CLAIM = 'user_type'

    USER_TYPE_REGULAR = "regular"
    USER_TYPE_MOBILE_ONLY = "mobile_only"

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        token[cls.USER_TYPE_CLAIM] = cls.USER_TYPE_REGULAR
        if isinstance(user, TigaUser):
            token[cls.USER_TYPE_CLAIM] = cls.USER_TYPE_MOBILE_ONLY

        return token

class SlidingToken(Token, OriginalSlidingToken):
    pass

class RefreshToken(Token, OriginalRefreshToken):
    pass