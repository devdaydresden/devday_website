from event.models import Event
from talk.models import Talk


def committee_member_context_processor(request):
    if request.user.is_authenticated:
        return {
            "is_committee_member": request.user.has_perms(
                ("talk.add_vote", "talk.add_talkcomment")
            )
        }
    else:
        return {"is_committee_member": False}


def reservation_context_processor(request):
    event = Event.objects.current_event()
    if event.sessions_published and not event.is_started():
        return {
            "reservable_sessions": Talk.objects.filter(
                event=event, track__isnull=False, spots__gt=0
            ).exists()
        }
    return {"reservable_sessions": False}
