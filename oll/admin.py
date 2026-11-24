from django.contrib import admin, messages
from django.utils.html import format_html

from .diagrams import generate_diagram
from .models import Algorithm, CaseOrientation, OLLCase, Transition


def diagram_img(orientation, size):
    if not orientation.diagram:
        return "—"

    return format_html(
        '<img src="{}" width="{}" height="{}" alt="{}">',
        orientation.diagram.url,
        size,
        size,
        orientation,
    )


def generate_for(modeladmin, request, orientations):
    count = 0
    for orientation in orientations:
        generate_diagram(orientation)
        count += 1

    modeladmin.message_user(
        request, f"Generated {count} SVG diagram{'s' if count != 1 else ''}.", messages.SUCCESS
    )


class CaseOrientationInline(admin.TabularInline):
    model = CaseOrientation
    extra = 0
    fields = ["rotation", "state", "diagram_preview"]
    readonly_fields = ["diagram_preview"]

    @admin.display(description="Diagram")
    def diagram_preview(self, obj):
        return diagram_img(obj, 60)


class OutgoingTransitionInline(admin.TabularInline):
    model = Transition
    fk_name = "start"
    extra = 0
    autocomplete_fields = ["algorithm", "end"]


@admin.register(OLLCase)
class OLLCaseAdmin(admin.ModelAdmin):
    list_display = ["number", "name", "group"]
    list_filter = ["group"]
    search_fields = ["name", "group"]
    inlines = [CaseOrientationInline]
    actions = ["generate_diagrams"]

    @admin.action(description="Generate SVG diagrams (all orientations)")
    def generate_diagrams(self, request, queryset):
        orientations = CaseOrientation.objects.filter(case__in=queryset).select_related("case")
        generate_for(self, request, orientations)


@admin.register(CaseOrientation)
class CaseOrientationAdmin(admin.ModelAdmin):
    list_display = ["case", "rotation", "state", "diagram_thumbnail"]
    list_filter = ["rotation"]
    list_select_related = ["case"]
    search_fields = ["state", "case__name"]
    readonly_fields = ["diagram", "diagram_preview"]
    inlines = [OutgoingTransitionInline]
    actions = ["generate_diagrams"]

    @admin.display(description="Diagram")
    def diagram_thumbnail(self, obj):
        return diagram_img(obj, 48)

    @admin.display(description="Preview")
    def diagram_preview(self, obj):
        return diagram_img(obj, 180)

    @admin.action(description="Generate SVG diagram")
    def generate_diagrams(self, request, queryset):
        generate_for(self, request, queryset.select_related("case"))


@admin.register(Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    list_display = ["moves", "name"]
    search_fields = ["moves", "name"]


@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ["start", "algorithm", "end"]
    list_select_related = ["start__case", "algorithm", "end__case"]
    autocomplete_fields = ["start", "algorithm", "end"]
