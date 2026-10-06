from django.db import models


def at_most_one_role(admin_field, manager_field, name):
    """
    CheckConstraint for an admin / manager FK pair: an action is done by an
    Admin or by a Manager, never both. Both empty is allowed (unknown, or the
    account was deleted).
    """
    return models.CheckConstraint(
        check=models.Q(**{f"{admin_field}__isnull": True})
        | models.Q(**{f"{manager_field}__isnull": True}),
        name=name,
    )
