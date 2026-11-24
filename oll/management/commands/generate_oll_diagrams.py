from django.core.management.base import BaseCommand

from oll.diagrams import generate_diagram
from oll.models import CaseOrientation


class Command(BaseCommand):
    help = "Generate SVG diagrams for OLL case orientations."

    def add_arguments(self, parser):
        parser.add_argument(
            "cases",
            nargs="*",
            type=int,
            help="OLL case numbers to generate (default: all).",
        )
        parser.add_argument(
            "--missing",
            action="store_true",
            help="Only generate orientations that have no diagram yet.",
        )

    def handle(self, *args, cases, missing, **options):
        orientations = CaseOrientation.objects.select_related("case")
        if cases:
            orientations = orientations.filter(case__number__in=cases)
        if missing:
            orientations = orientations.filter(diagram="")

        count = 0
        for orientation in orientations:
            path = generate_diagram(orientation)
            count += 1
            if options["verbosity"] >= 2:
                self.stdout.write(path)
        if options["verbosity"] >= 1:
            self.stdout.write(self.style.SUCCESS(f"Generated {count} diagram(s)."))
