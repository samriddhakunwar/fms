from .models import ActivityLog


def _object_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class ViewLoggingMixin:
    """
    ViewSet mixin: a successful list/retrieve by one of view_log_roles writes
    an activity_log VIEW row for view_log_target. Covers the view-only
    requirements (Staff viewing stock, Manager viewing staff and sales).
    """

    view_log_target = ""
    view_log_roles: tuple = ()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self.log_view(request, response)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        lookup = self.lookup_url_kwarg or self.lookup_field
        self.log_view(request, response, _object_id(kwargs.get(lookup)))
        return response

    def log_view(self, request, response, object_id=None):
        if response.status_code != 200:
            return
        if getattr(request.user, "role", None) not in self.view_log_roles:
            return
        ActivityLog.record(request, ActivityLog.Action.VIEW, self.view_log_target, object_id)
