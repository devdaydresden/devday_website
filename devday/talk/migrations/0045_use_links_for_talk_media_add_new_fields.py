from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('talk', '0044_auto_20200310_2010'),
    ]

    operations = [
        migrations.AddField(
            model_name='talkmedia',
            name='code',
            field=models.URLField(blank=True, verbose_name='Source code'),
        ),
        migrations.AddField(
            model_name='talkmedia',
            name='slides',
            field=models.URLField(blank=True, verbose_name='Slides'),
        ),
        migrations.AddField(
            model_name='talkmedia',
            name='video',
            field=models.URLField(blank=True, verbose_name='Video'),
        ),
    ]
