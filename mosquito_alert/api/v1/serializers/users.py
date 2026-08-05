from uuid import UUID

from rest_framework import serializers
from django.contrib.auth import get_user_model

from mosquito_alert.users.models import TigaUser


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class UserScoreSerializer(serializers.ModelSerializer):
        value = serializers.IntegerField(source="score_v2", min_value=0, read_only=True)
        updated_at = serializers.DateTimeField(
            source="last_score_update", read_only=True, allow_null=True
        )

        class Meta:
            model = TigaUser
            fields = ("value", "updated_at")

    uuid = serializers.UUIDField(source="user_UUID", read_only=True)
    language_iso = serializers.SerializerMethodField(
        help_text="ISO 639-1 code", default="en"
    )
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_guest = serializers.SerializerMethodField()
    score = UserScoreSerializer(source="*", read_only=True)

    def get_is_guest(self, obj) -> bool:
        return True

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_first_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.first_name
        return "Anonymous"

    def get_last_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.last_name
        return "User"

    def get_full_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.get_full_name()
        return "Anonymous User"

    def get_language_iso(self, obj) -> str:
        return obj.language_iso2

    def to_representation(self, instance):
        if isinstance(instance, User):
            # NOTE: this must be the same structure as defined.
            data = {}
            data["uuid"] = UUID(int=instance.pk)
            data["username"] = instance.get_username()
            data["first_name"] = self.get_first_name(obj=instance)
            data["last_name"] = self.get_last_name(obj=instance)
            data["full_name"] = self.get_full_name(obj=instance)
            data["registration_time"] = instance.date_joined
            data["locale"] = "en"
            data["language_iso"] = "en"
            data["is_guest"] = False
            data["score"] = {"value": 0, "updated_at": None}
            return {k: v for k, v in data.items() if k in self.fields.keys()}

        return super().to_representation(instance)

    class Meta:
        model = TigaUser
        fields = (
            "uuid",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "registration_time",
            "locale",
            "language_iso",
            "is_guest",
            "score",
        )
        read_only_fields = (
            "registration_time",
            "score",
        )
        extra_kwargs = {
            "locale": {"default": "en"},
        }


class SimpleUserSerializer(UserSerializer):
    uuid = serializers.SerializerMethodField()

    def get_uuid(self, obj) -> UUID:
        return UUID(int=obj.pk)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ("uuid", "username", "first_name", "last_name", "full_name")


class MinimalUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("uuid", "locale")
