from talk.models import Talk, Speaker


def create_test_talk(speaker):
    return Talk.objects.create(speaker=speaker)


def create_test_speaker(attendee):
    return Speaker.objects.create(user=attendee, videopermission=True, shirt_size=0)
