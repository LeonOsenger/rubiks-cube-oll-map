import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .diagrams import GREY, SIDE_COLORS, YELLOW, diagram_filename, render_svg, sticker_colors
from .models import CaseOrientation, OLLCase

RED, GREEN, ORANGE, BLUE = (hex_ for _, hex_ in SIDE_COLORS)


class StickerColorsTests(TestCase):
    def test_solved_is_all_yellow_on_top(self):
        top, sides = sticker_colors("00000000", 0)
        self.assertEqual(top, [[YELLOW] * 3] * 3)
        self.assertEqual(sides, {"F": [RED] * 3, "R": [GREEN] * 3, "B": [ORANGE] * 3,
                                 "L": [BLUE] * 3})  # fmt: skip

    def test_side_colours_follow_rotation(self):
        expected = {
            0: (RED, GREEN, ORANGE, BLUE),
            1: (GREEN, ORANGE, BLUE, RED),
            2: (ORANGE, BLUE, RED, GREEN),
            3: (BLUE, RED, GREEN, ORANGE),
        }
        for rotation, colours in expected.items():
            _, sides = sticker_colors("00000000", rotation)
            self.assertEqual(tuple(sides[face][1] for face in "FRBL"), colours)

    def test_oll_1_has_bars_left_and_right(self):
        top, sides = sticker_colors("11111212", 0)
        self.assertEqual(top, [[GREY, GREY, GREY], [GREY, YELLOW, GREY], [GREY, GREY, GREY]])
        self.assertEqual(sides["L"], [YELLOW] * 3)
        self.assertEqual(sides["R"], [YELLOW] * 3)
        self.assertEqual(sides["F"], [RED, YELLOW, RED])
        self.assertEqual(sides["B"], [ORANGE, YELLOW, ORANGE])

    def test_corner_twist_directions(self):
        # UFR twisted: 1 -> yellow on R, 2 -> yellow on F.
        _, sides = sticker_colors("00000010", 0)
        self.assertEqual(sides["R"][2], YELLOW)
        self.assertEqual(sides["F"][2], RED)
        _, sides = sticker_colors("00000020", 0)
        self.assertEqual(sides["F"][2], YELLOW)
        self.assertEqual(sides["R"][2], GREEN)

    def test_render_svg_is_svg(self):
        svg = render_svg("11111212", 0, title="OLL 1 <dot>")
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("<title>OLL 1 &lt;dot&gt;</title>", svg)
        self.assertEqual(svg.count("<rect"), 1 + 9 + 12)


class DiagramStorageTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)

        self.case = OLLCase.objects.create(number=27, name="Sune")
        self.orientations = [
            CaseOrientation.objects.create(case=self.case, rotation=r, state=s)
            for r, s in enumerate(["00001110", "00000111", "00001011", "00001101"])
        ]

    def test_filenames(self):
        self.assertEqual(
            [diagram_filename(o) for o in self.orientations],
            [
                "oll-27_rot000_red-front.svg",
                "oll-27_rot090_green-front.svg",
                "oll-27_rot180_orange-front.svg",
                "oll-27_rot270_blue-front.svg",
            ],
        )

    def test_command_generates_and_regenerates_with_stable_name(self):
        call_command("generate_oll_diagrams", verbosity=0)
        first = CaseOrientation.objects.get(pk=self.orientations[1].pk)
        self.assertEqual(first.diagram.name, "oll/diagrams/oll-27_rot090_green-front.svg")
        with first.diagram.open("rb") as fh:
            self.assertIn(b"<svg", fh.read())

        call_command("generate_oll_diagrams", "27", verbosity=0)
        again = CaseOrientation.objects.get(pk=first.pk)
        self.assertEqual(again.diagram.name, first.diagram.name)

    def test_command_missing_only(self):
        call_command("generate_oll_diagrams", verbosity=0)
        CaseOrientation.objects.filter(rotation=0).update(diagram="")
        call_command("generate_oll_diagrams", "--missing", verbosity=0)
        self.assertFalse(CaseOrientation.objects.filter(diagram="").exists())

    def test_admin_actions(self):
        user = get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        self.client.force_login(user)

        response = self.client.post(
            reverse("admin:oll_ollcase_changelist"),
            {"action": "generate_diagrams", "_selected_action": [self.case.pk]},
            follow=True,
        )
        self.assertContains(response, "Generated 4 SVG diagrams.")
        self.assertFalse(CaseOrientation.objects.filter(diagram="").exists())

        response = self.client.get(reverse("admin:oll_caseorientation_changelist"))
        self.assertContains(response, "oll-27_rot180_orange-front.svg")
        response = self.client.get(
            reverse("admin:oll_caseorientation_change", args=[self.orientations[0].pk])
        )
        self.assertContains(response, 'width="180"')
