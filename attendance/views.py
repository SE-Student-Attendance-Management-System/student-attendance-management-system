from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """
    Authenticated landing view (Issue #11).
    Displays the authenticated user's details and session actions.
    Role-specific dashboards will be introduced in Issue #12.
    """
    return render(request, "home.html", {"user": request.user})
