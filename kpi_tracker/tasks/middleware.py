from django.contrib.auth import login
from django.contrib.auth.models import User


class AutoLoginMiddleware:
    """Automatically authenticate the superuser on every request.

    For a single-user standalone desktop app there is no need for a login
    screen.  This middleware silently logs in the first superuser before the
    view runs, so @login_required decorators still work without ever showing
    the login page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            try:
                user = User.objects.filter(is_superuser=True).first()
                if user:
                    login(request, user,
                          backend='django.contrib.auth.backends.ModelBackend')
            except Exception:
                pass
        return self.get_response(request)
