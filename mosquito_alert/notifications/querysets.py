from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, QuerySet


class NotificationSubscriptionQuerySet(QuerySet):
    def _filter_generic_field(self, obj, content_type_fieldname, object_id_fieldname, allow_null=False):
        q_nullable = Q(**{f"{content_type_fieldname}__isnull": True})
        if obj is None:
            q = q_nullable
        else:
            content_type = ContentType.objects.get_for_model(obj).pk
            q = Q(
                **{
                    f"{content_type_fieldname}": content_type,
                    f"{object_id_fieldname}": obj.pk,
                }
            )

            if allow_null:
                q |= q_nullable

        return self.filter(q)

    def for_actor(self, obj):
        return self._filter_generic_field(
            obj=obj,
            content_type_fieldname="actor_content_type",
            object_id_fieldname="actor_object_id",
        )

    def for_target(self, obj, allow_null=False):
        return self._filter_generic_field(
            obj=obj,
            content_type_fieldname="target_content_type",
            object_id_fieldname="target_object_id",
            allow_null=allow_null,
        )
