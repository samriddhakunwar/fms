"""
The user behind the current API request, for code that runs below the view,
and helpers that turn a login into the Admin / Manager record it acts as.

SaleItem.save and the SaleItem pre_delete signal log stock movements but never
see the request; views using ActorMixin publish request.user here so those rows
record who made the change. Outside such a request (Django admin, management
commands) the actor is None and callers fall back to their own default.

Who-did-what columns point at the role tables (admin / manager), not at user,
so each one comes as a pair: role_fields(user, "created_by_") gives
{"created_by_admin": <AdminProfile or None>, "created_by_manager": ...}.
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
        self._actor_token = _current_actor.set(
            user if user and user.is_authenticated else None
        )

    def finalize_response(self, request, response, *args, **kwargs):
        self._reset_actor()
        return super().finalize_response(request, response, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # finalize_response is skipped when an exception escapes DRF's handler;
        # never let the actor leak into the next request on this thread.
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            self._reset_actor()

    def _reset_actor(self):
        if self._actor_token is not None:
            _current_actor.reset(self._actor_token)
            self._actor_token = None
