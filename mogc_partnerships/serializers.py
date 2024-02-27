from django.contrib.auth import get_user_model

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
        fields = ["course_key", "title", "description", "short_description"]


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


class PartnerCohortSerializer(serializers.ModelSerializer):
    """Serializer for PartnerCohort objects."""

    partner = serializers.SlugRelatedField(
        slug_field="slug", queryset=models.Partner.objects.active()
    )
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = models.PartnerCohort
        fields = ["partner", "name", "uuid"]


class PartnerCohortUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PartnerCohort object updates."""

    partner = serializers.ReadOnlyField(source="partner.slug")
    uuid = serializers.ReadOnlyField()

    class Meta:
        model = models.PartnerCohort
        fields = ["partner", "name", "uuid"]


class CohortOfferingSerializer(serializers.ModelSerializer):
    """Serializer for CohortOffering objects."""

    cohort = serializers.ReadOnlyField(source="cohort.uuid")
    partner = serializers.ReadOnlyField(source="cohort.partner.slug")
    details = PartnerOfferingDetailsSerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField(method_name="get_is_enrolled")

    class Meta:
        model = models.CohortOffering
        fields = [
            "id",
            "cohort",
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


class CohortMembershipListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        cohort = self.context.get("cohort")
        member_emails = [o["email"] for o in validated_data]

        User = get_user_model()
        membership_accounts = User.objects.filter(
            email__in=[email for email in member_emails]
        ).values_list()
        account_email_map = {user.email: user for user in membership_accounts}

        cohort_memberships = [
            models.CohortMembership(
                user=account_email_map.get(member_email),
                cohort=cohort,
                email=member_email,
            )
            for member_email in member_emails
        ]

        objects = models.CohortMembership.objects.bulk_create(
            cohort_memberships, ignore_conflicts=True
        )
        # bulk_create doesn't return autoincremented IDs with MySQL DBs
        # so we have to query results separately
        return models.CohortMembership.objects.filter(
            email__in=[cm.email for cm in objects],
            cohort=cohort
        )


class CohortMembershipSerializer(serializers.ModelSerializer):
    """Serializer for CohortMembership objects."""

    id = serializers.ReadOnlyField()
    cohort = serializers.ReadOnlyField(source="cohort.uuid")
    partner = serializers.ReadOnlyField(source="cohort.partner.slug")
    user = serializers.ReadOnlyField(source="user.username")
    name = serializers.ReadOnlyField(source="user.profile.name")

    class Meta:
        model = models.CohortMembership
        fields = ["id", "cohort", "partner", "email", "user", "name"]
        list_serializer_class = CohortMembershipListSerializer

    def create(self, validated_data):
        validated_data["cohort"] = self.context.get("cohort")

        User = get_user_model()
        try:
            validated_data["user"] = User.objects.get(email=validated_data.get("email"))
        except User.DoesNotExist:
            validated_data["user"] = None

        return models.CohortMembership.objects.create(**validated_data)


class EnrollmentRecordSerializer(serializers.ModelSerializer):
    """Serializer for EnrollmentRecord objects."""

    id = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source="user.username")
    offering = PartnerOfferingSerializer(read_only=True)

    class Meta:
        model = models.EnrollmentRecord
        fields = ["id", "user", "offering", "is_complete"]
