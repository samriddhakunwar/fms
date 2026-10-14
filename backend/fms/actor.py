"""
Who is acting: the request user for code below the view, and helpers that turn
a login into the Admin / Manager record it acts as.

SaleItem.save and its pre_delete signal log stock movements but never see the
request (a queryset delete cannot take arguments), so views using ActorMixin
publish request.user here. Outside such a request (Django admin, management
commands) the actor is None and callers fall back to their own default.
"""

from contextvars import ContextVar

_current_actor = ContextVar("current_actor", default=None)


def get_current_actor():
    return _current_actor.get()


def admin_of(user):
    """The user's Admin record, or None (anonymous, or not an Admin)."""
    if user is None or not user.is_authenticated:
        return None
    return getattr(user, "admin_profile", None)


def manager_of(user):
    """The user's Manager record, or None (anonymous, or not a Manager)."""
    if user is None or not user.is_authenticated:
        return None
    return getattr(user, "manager_profile", None)


def role_fields(user, prefix=""):
    """The <prefix>admin / <prefix>manager pair for a user; at most one is set."""
    return {f"{prefix}admin": admin_of(user), f"{prefix}manager": manager_of(user)}


def stamp(obj, user, prefix):
    """Set obj's <prefix>admin / <prefix>manager pair from user; returns the field names."""
    fields = role_fields(user, prefix)
    for field, profile in fields.items():
        setattr(obj, field, profile)
    return list(fields)


def role_name(admin, manager):
    """Display name of whichever of an admin / manager pair is set."""
    profile = admin or manager
    return str(profile) if profile else None


class ActorMixin:
    """DRF view mixin: makes request.user the current actor for the request."""

    _actor_token = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = request.user
        self._actor_token = _current_actor.set(user if user and user.is_authenticated else None)

    def dispatch(self, request, *args, **kwargs):
        # finally, not finalize_response: the actor must never leak into the
        # next request on this thread, even when an exception escapes.
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            if self._actor_token is not None:
                _current_actor.reset(self._actor_token)
                self._actor_token = None
