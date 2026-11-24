"""Data model for mapping OLL cases and the algorithms that connect them."""

from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

STATE_VALIDATOR = RegexValidator(
    regex=r"^[01]{4}[012]{4}$",
    message="State must be 4 edge digits (0/1) followed by 4 corner digits (0/1/2).",
)


class OLLCase(models.Model):
    """One of the 57 OLL cases (1–57), or 0 for the solved top layer."""

    number = models.PositiveSmallIntegerField(
        unique=True,
        validators=[MaxValueValidator(57)],
    )
    name = models.CharField(max_length=50, blank=True)
    group = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "OLL case"
        constraints = [
            models.CheckConstraint(condition=Q(number__lte=57), name="oll_case_number_range"),
        ]

    def __str__(self):
        label = f"OLL {self.number}"
        return f"{label} ({self.name})" if self.name else label


class CaseOrientation(models.Model):
    """An OLL case viewed with a specific side in front."""

    class Rotation(models.IntegerChoices):
        R0 = 0, "0°"
        R90 = 1, "90°"
        R180 = 2, "180°"
        R270 = 3, "270°"

    case = models.ForeignKey(OLLCase, on_delete=models.CASCADE, related_name="orientations")
    rotation = models.PositiveSmallIntegerField(
        choices=Rotation.choices,
        help_text="Clockwise U quarter turns",
    )
    state = models.CharField(
        max_length=8,
        unique=True,
        validators=[STATE_VALIDATOR],
        help_text="Edges UB UR UF UL (0/1) + corners UBL UBR UFR UFL (0/1/2).",
    )
    diagram = models.FileField(
        upload_to="oll/diagrams/",
        blank=True,
        help_text="Generated SVG (admin action or `manage.py generate_oll_diagrams`).",
    )

    class Meta:
        ordering = ["case__number", "rotation"]
        constraints = [
            models.UniqueConstraint(fields=["case", "rotation"], name="unique_case_rotation"),
            models.CheckConstraint(condition=Q(rotation__lte=3), name="orientation_rotation_range"),
        ]

    def __str__(self):
        return f"{self.case} @ {self.get_rotation_display()}"


class Algorithm(models.Model):
    """A move sequence, reusable across any number of case orientations."""

    moves = models.CharField(max_length=200, unique=True, help_text="e.g. R U R' U R U2 R'")
    name = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["moves"]

    def __str__(self):
        return f"{self.name}: {self.moves}" if self.name else self.moves


class Transition(models.Model):
    """Executing ``algorithm`` from ``start`` lands on ``end``.

    A start orientation can have many algorithms; each (start, algorithm) pair has
    exactly one end orientation.
    """

    start = models.ForeignKey(
        CaseOrientation, on_delete=models.CASCADE, related_name="outgoing_transitions"
    )
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE, related_name="transitions")
    end = models.ForeignKey(
        CaseOrientation, on_delete=models.CASCADE, related_name="incoming_transitions"
    )

    class Meta:
        ordering = ["start", "algorithm"]
        constraints = [
            models.UniqueConstraint(fields=["start", "algorithm"], name="unique_start_algorithm"),
        ]

    def __str__(self):
        return f"{self.start} --[{self.algorithm.moves}]--> {self.end}"
