from django.dispatch import Signal

attendence_cancelled = Signal(providing_args=["attendee", "request"])
