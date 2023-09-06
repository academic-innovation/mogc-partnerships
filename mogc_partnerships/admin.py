from django.contrib import admin

from . import models


class MangerInline(admin.TabularInline):
    model = models.PartnerManagementMembership
    fields = ("user",)
    autocomplete_fields = ("user",)


class OfferingInline(admin.StackedInline):
    model = models.PartnerOffering
    fields = ("course_key", "title", "short_description", "description")


@admin.register(models.Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    fields = ("name", "slug", "org", "is_active")
    inlines = [MangerInline, OfferingInline]


@admin.register(models.PartnerManagementMembership)
class PartnerManagementMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "partner")


@admin.register(models.PartnerOffering)
class PartnerOfferingAdmin(admin.ModelAdmin):
    list_display = ("title", "course_key", "partner")


@admin.register(models.PartnerCohort)
class PartnerCohortAdmin(admin.ModelAdmin):
    list_display = ("name", "uuid", "partner", "is_active")


@admin.register(models.CohortOffering)
class CohortOfferingAdmin(admin.ModelAdmin):
    list_display = ("cohort", "offering")


@admin.register(models.CohortMembership)
class CohortMembershipAdmin(admin.ModelAdmin):
    list_display = ("email", "cohort", "is_activated")

    @admin.display(boolean=True)
    def is_activated(self, membership):
        return membership.activated


@admin.register(models.EnrollmentRecord)
class EnrollmentRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "offering", "mode")
