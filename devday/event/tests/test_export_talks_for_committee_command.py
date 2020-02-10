import io
import os

from django.core.files.temp import NamedTemporaryFile
from django.test import TestCase

from django.core.management import call_command

from devday.utils.devdata import DevData
from event.models import Event


class TestExportTalksForCommitteeCommand(TestCase):
    def test_export_with_no_talks(self):
        outbuf = io.StringIO()
        errbuf = io.StringIO()
        call_command("export_talks_for_committee", stdout=outbuf, stderr=errbuf)
        self.assertEqual("", outbuf.getvalue().strip())
        self.assertEqual("No talks found for current event", errbuf.getvalue().strip())

    def test_export_with_talks(self):
        dev_data = DevData()
        dev_data.SPEAKERS_PER_EVENT = 2
        events = [Event.objects.current_event()]
        dev_data.create_users_and_attendees(10, events=events)
        dev_data.create_speakers(events)
        dev_data.create_talk_formats()
        dev_data.create_talks(events=events)
        talks = Event.objects.current_event().talk_set
        outbuf = io.StringIO()
        errbuf = io.StringIO()
        call_command("export_talks_for_committee", stdout=outbuf, stderr=errbuf)
        output_lines = outbuf.getvalue().splitlines()
        self.assertEqual(talks.count() + 1, len(output_lines))
        self.assertEqual("", errbuf.getvalue().strip())

    def test_export_with_talks_csv_file(self):
        dev_data = DevData()
        dev_data.SPEAKERS_PER_EVENT = 2
        events = [Event.objects.current_event()]
        dev_data.create_users_and_attendees(10, events=events)
        dev_data.create_speakers(events)
        dev_data.create_talk_formats()
        dev_data.create_talks(events=events)
        talks = Event.objects.current_event().talk_set
        outbuf = io.StringIO()
        errbuf = io.StringIO()
        tempfile = NamedTemporaryFile(mode="w", delete=False)
        try:
            call_command("export_talks_for_committee", csv_file=tempfile, stdout=outbuf, stderr=errbuf)
            tempfile.close()
            self.assertEqual("", outbuf.getvalue().strip())
            self.assertEqual("", errbuf.getvalue().strip())
            with open(tempfile.name, "r") as output:
                output_lines = output.read().splitlines()
                self.assertEqual(talks.count() + 1, len(output_lines))
        finally:
            os.unlink(tempfile.name)
