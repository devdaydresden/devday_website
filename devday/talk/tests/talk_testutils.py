from talk.models import Talk


def create_test_talk(speaker, event):
    return Talk.objects.create(draft_speaker=speaker, event=event)
