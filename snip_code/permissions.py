from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import HttpRequest

def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            if not request.user.has_perm(permission):
                raise PermissionDenied("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
