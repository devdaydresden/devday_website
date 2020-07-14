import requests
from bs4 import BeautifulSoup
from django.db import migrations, models


def migrate_code_links(apps, schema_editor):
    TalkMedia = apps.get_model("talk", "TalkMedia")

    db_alias = schema_editor.connection.alias
    for media in TalkMedia.objects.using(db_alias).exclude(codelink__exact=''):
        media.code = media.codelink
        media.save()


def migrate_slideshare_links(apps, schema_editor):
    TalkMedia = apps.get_model("talk", "TalkMedia")

    http_session = requests.Session()

    base_url = 'https://www.slideshare.net/slideshow/embed_code/key/'
    db_alias = schema_editor.connection.alias
    for media in TalkMedia.objects.using(db_alias).exclude(slideshare__exact=''):
        response = http_session.get(base_url + media.slideshare)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        link = soup('link', rel='canonical')[0]
        media.slides = link.get('href')
        media.save()


def migrate_youtube_links(apps, schema_editor):
    TalkMedia = apps.get_model("talk", "TalkMedia")

    db_alias = schema_editor.connection.alias
    for media in TalkMedia.objects.using(db_alias).exclude(youtube__exact=''):
        media.video = "https://www.youtube.com/watch?v={}".format(media.youtube)
        media.save()


class Migration(migrations.Migration):

    dependencies = [
        ('talk', '0045_use_links_for_talk_media_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_code_links),
        migrations.RunPython(migrate_slideshare_links),
        migrations.RunPython(migrate_youtube_links),
    ]
