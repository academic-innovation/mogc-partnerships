from rest_framework import serializers

from . import models


class PartnerOfferingSerializer(serializers.ModelSerializer):
    """Serializer for PartnerOffering objects."""

    partner = serializers.ReadOnlyField(source="partner.slug")

    class Meta:
        model = models.PartnerOffering
        fields = ["id", "partner", "course_key", "title"]


class PartnerOfferingDetailsSerializer(serializers.ModelSerializer):
    """Serializer for embedded PartnerOffering details."""

    class Meta:
        model = models.PartnerOffering
        fields = ["course_key", "title"]


class PartnerSerializer(serializers.ModelSerializer):
    """Serializer for Partner objects."""

    offerings = PartnerOfferingSerializer(many=True, read_only=True)
    is_manager = serializers.SerializerMethodField(method_name="get_is_manager")

    class Meta:
        model = models.Partner
        fields = ["name", "slug", "offerings", "is_manager"]

    def get_is_manager(self, obj):
        context = self.context
        if "associations" not in context:
            return False
        return obj.id in context["associations"]


class PartnerCatalogSerializer(serializers.ModelSerializer):
    """Serializer for PartnerCatalog objects."""

    partner = serializers.SlugRelatedField(
        slug_field="slug", queryset=models.Partner.objects.active()
    )
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = models.PartnerCatalog
        fields = ["partner", "name", "uuid"]


class PartnerCatalogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PartnerCatalog object updates."""

    partner = serializers.ReadOnlyField(source="partner.slug")
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = models.PartnerCatalog
        fields = ["partner", "name", "uuid"]


class CatalogOfferingSerializer(serializers.ModelSerializer):
    """Serializer for CatalogOffering objects."""

    catalog = serializers.ReadOnlyField(source="catalog.uuid")
    partner = serializers.ReadOnlyField(source="catalog.partner.slug")
    details = PartnerOfferingDetailsSerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField(method_name="get_is_enrolled")

    class Meta:
        model = models.CatalogOffering
        fields = [
            "id",
            "catalog",
            "partner",
            "offering",
            "details",
            "is_enrolled",
            "continue_learning_url",
        ]

    def get_is_enrolled(self, obj):
        context = self.context
        if "enrollments" not in context:
            return False
        return obj.offering_id in context["enrollments"]


class CatalogMembershipSerializer(serializers.ModelSerializer):
    """Serializer for CatalogMembership objects."""

    id = serializers.ReadOnlyField()
    catalog = serializers.ReadOnlyField(source="catalog.uuid")
    partner = serializers.ReadOnlyField(source="catalog.partner.slug")
    user = serializers.ReadOnlyField(source="user.username")
    name = serializers.ReadOnlyField(source="user.profile.name")

    class Meta:
        model = models.CatalogMembership
        fields = ["id", "catalog", "partner", "email", "user", "name"]


class EnrollmentRecordSerializer(serializers.ModelSerializer):
    """Serializer for EnrollmentRecord objects."""

    id = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source="user.username")
    offering = PartnerOfferingSerializer(read_only=True)

    class Meta:
        model = models.EnrollmentRecord
        fields = ["id", "user", "offering", "is_complete"]
