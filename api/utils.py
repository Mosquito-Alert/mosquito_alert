from typing import List


def get_fk_fieldnames(model, related_model) -> List:
    user_fk_fieldnames = []
    for field in model._meta.get_fields():
        if field.is_relation and field.related_model == related_model:
            user_fk_fieldnames.append(field.name)
    return user_fk_fieldnames
