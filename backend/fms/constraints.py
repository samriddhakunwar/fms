from django.db import models


def at_most_one_role(admin_field, manager_field, name):
    """
    CheckConstraint for an admin / manager FK pair: an action is done by an
    Admin or by a Manager, never both. Both empty is allowed (unknown, or the
    account was deleted).
    """
    return models.CheckConstraint(  # pyright: ignore[reportCallIssue]  Django 4.2 uses check=
        check=models.Q(**{f"{admin_field}__isnull": True})  # pyright: ignore[reportCallIssue]
        | models.Q(**{f"{manager_field}__isnull": True}),
        name=name,
    )
