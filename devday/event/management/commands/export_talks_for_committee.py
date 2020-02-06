"""
A management command to export the list of submitted talks to be used in program
committee meetings.
"""

import argparse
import csv

from django.core.management import BaseCommand
from django.db.models import Avg, Count

from event.models import Event


class Command(BaseCommand):
    help = "Export a list of submitted talks including ratings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-file",
            dest="csv_file",
            type=argparse.FileType("w"),
            help="CSV file that the export data should be written to",
        )

    def handle(self, *args, **options):
        talks = (
            Event.objects.current_event()
                .talk_set.all()
                .prefetch_related('talkcomment_set')
                .annotate(num_votes=Count("vote"), avg_votes=Avg("vote__score"))
            .order_by("-avg_votes", "title")
        )

        if not talks.exists():
            self.stderr.write("No talks found for current event")
            return

        outfile = options["csv_file"]
        if outfile is None:
            outfile = self.stdout

        out = csv.writer(outfile, dialect=csv.excel, lineterminator="\n")
        out.writerow(("Speaker", "Title", "Abstract", "Votes", "Avg. Score", "Comments"))
        for t in talks:
            row = (
                t.draft_speaker.name, t.title, t.abstract, t.num_votes, t.avg_votes,
                "\n".join([f"{v.created} {v.commenter.email}: {v.comment}" for v in
                           t.talkcomment_set.order_by('created').all()]))
            out.writerow(row)
