from django.db import OperationalError, ProgrammingError
from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    try:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        recent = list(Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10])
    except (OperationalError, ProgrammingError):
        return {'notif_unread_count': 0, 'notif_recent': []}
    return {
        'notif_unread_count': unread_count,
        'notif_recent': recent,
    }
