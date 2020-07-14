from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('talk', '0046_use_links_for_talk_media_migrate_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='talkmedia',
            name='codelink',
        ),
        migrations.RemoveField(
            model_name='talkmedia',
            name='slideshare',
        ),
        migrations.RemoveField(
            model_name='talkmedia',
            name='youtube',
        ),
    ]
