# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-22 08:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('talk', '0034_remove_old_speaker_model_and_tighten_constraints'),
    ]

    operations = [
        migrations.RunSQL(
            """
            INSERT INTO talk_room (created, modified, name, priority, event_id)
            SELECT DISTINCT current_timestamp,
                            current_timestamp,
                            r.name,
                            r.priority,
                            t.event_id
            FROM talk_talk t
                   JOIN talk_talkslot s ON s.talk_id = t.id
                   JOIN talk_room r ON r.id = s.room_id
            WHERE t.event_id <> r.event_id;
            """),
        migrations.RunSQL(
            """
            WITH wrong_slots AS (SELECT DISTINCT t.event_id, s.id, r.name
                                 FROM talk_talkslot s
                                        JOIN talk_room r ON s.room_id = r.id
                                        JOIN talk_talk t ON s.talk_id = t.id
                                 WHERE t.event_id <> r.event_id)
            UPDATE talk_talkslot
            SET modified = current_timestamp,
                room_id  = (SELECT id
                            FROM talk_room
                            WHERE event_id = wrong_slots.event_id
                              AND name = wrong_slots.name)
            FROM wrong_slots
            WHERE talk_talkslot.id = wrong_slots.id;
            """),
    ]
