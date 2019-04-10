from talk.models import Talk


def create_test_talk(speaker, event, title, **kwargs):
    return Talk.objects.create(
        draft_speaker=speaker, event=event, title=title, **kwargs
    )
