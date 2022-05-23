from django.contrib import admin

from . import models


@admin.register(models.Partner)
class PartnerAdmin(admin.ModelAdmin):
    ...


@admin.register(models.PartnerManagementMembership)
class PartnerManagementMembershipAdmin(admin.ModelAdmin):
    ...


@admin.register(models.PartnerOffering)
class PartnerOfferingAdmin(admin.ModelAdmin):
    ...


@admin.register(models.PartnerCatalog)
class PartnerCatalogAdmin(admin.ModelAdmin):
    ...


@admin.register(models.CatalogOffering)
class CatalogOfferingAdmin(admin.ModelAdmin):
    ...


@admin.register(models.CatalogMembership)
class CatalogMembershipAdmin(admin.ModelAdmin):
    ...


@admin.register(models.EnrollmentRecord)
class EnrollmentRecordAdmin(admin.ModelAdmin):
    ...
