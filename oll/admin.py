from django.contrib import admin

from .models import Algorithm, CaseOrientation, OLLCase, Transition


class CaseOrientationInline(admin.TabularInline):
    model = CaseOrientation
    extra = 0


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


@admin.register(CaseOrientation)
class CaseOrientationAdmin(admin.ModelAdmin):
    list_display = ["case", "rotation", "state"]
    list_filter = ["rotation"]
    search_fields = ["state", "case__name"]
    inlines = [OutgoingTransitionInline]


@admin.register(Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    list_display = ["moves", "name"]
    search_fields = ["moves", "name"]


@admin.register(Transition)
class TransitionAdmin(admin.ModelAdmin):
    list_display = ["start", "algorithm", "end"]
    list_select_related = ["start__case", "algorithm", "end__case"]
    autocomplete_fields = ["start", "algorithm", "end"]
