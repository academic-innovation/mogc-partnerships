from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from opaque_keys.edx.django.models import CourseKeyField

from . import enums


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PartnerQuerySet(models.QuerySet):
    """Custom QuerySet for Partner objects."""

    def active(self):
        """Keeps only partners marked as active."""
        return self.filter(is_active=True)

    def for_user(self, user):
        """Keeps only partners where the given user is a manager or member."""
        user_cohort_memberships = user.memberships.all()
        membership_partner_ids = user_cohort_memberships.values_list(
            "cohort__partner_id", flat=True
        )
        management_partner_ids = user.partners.values_list("id", flat=True)
        all_partner_ids = list(membership_partner_ids) + list(management_partner_ids)
        return self.filter(id__in=all_partner_ids)


class Partner(TimeStampedModel):
    """A partner offering courses through Global Classroom."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    org = models.CharField(
        max_length=255,
        unique=True,
        help_text="The Open edX orginization code associated with this partner.",
    )
    is_active = models.BooleanField(default=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="PartnerManagementMembership",
        related_name="partners",
    )

    objects = PartnerQuerySet.as_manager()

    def __str__(self):
        return self.name


class PartnerManagementMembership(TimeStampedModel):
    partner = models.ForeignKey(
        Partner, related_name="management_memberships", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="management_memberships",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["partner", "user"], name="unique_user_per_partner"
            )
        ]

    def __str__(self):
        return f"{self.user} [{self.partner}]"


class PartnerOffering(TimeStampedModel):
    """A course that a partner may offer to its members."""

    partner = models.ForeignKey(
        Partner, related_name="offerings", on_delete=models.CASCADE
    )
    course_key = CourseKeyField(max_length=255)
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500)
    description = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["partner", "course_key"], name="unique_course_key_per_partner"
            )
        ]

    def __str__(self):
        return f"{self.course_key} [{self.partner}]"


class PartnerCohort(TimeStampedModel):
    """A grouping of course offerings made available to learners by a partner."""

    partner = models.ForeignKey(
        Partner, related_name="cohorts", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid4)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.uuid})"


class CohortOffering(TimeStampedModel):
    """A course offered to learners through a cohort."""

    cohort = models.ForeignKey(
        PartnerCohort, related_name="offerings", on_delete=models.CASCADE
    )
    offering = models.ForeignKey(PartnerOffering, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cohort", "offering"], name="unique_offering_per_cohort"
            )
        ]

    def __str__(self):
        return f"{self.offering.course_key} in {self.cohort.name}"

    @property
    def details(self):
        return self.offering

    @property
    def continue_learning_url(self):
        return reverse(
            "mogc_partnerships:continue_learning", kwargs={"offering_id": self.id}
        )


class CohortMembershipQuerySet(models.QuerySet):
    """Custom QuerySet for CohortMembership objects."""

    def pending(self):
        return self.filter(user=None)


class CohortMembership(TimeStampedModel):
    """A learner's membership in a cohort.

    Memberships without an associated user are considered to be invites. When a user
    with a matching email registers they will be associated with the membership.
    """

    cohort = models.ForeignKey(
        PartnerCohort, related_name="memberships", on_delete=models.CASCADE
    )
    email = models.EmailField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="memberships",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=True)

    objects = CohortMembershipQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cohort", "email"], name="unique_email_per_cohort"
            ),
            models.UniqueConstraint(
                fields=["cohort", "user"], name="unique_user_per_cohort"
            ),
        ]

    @property
    def status(self):
        if not self.active:
            return enums.CohortMembershipStatus.DEACTIVATED.value
        if self.user is not None:
            return enums.CohortMembershipStatus.ACTIVATED.value
        return enums.CohortMembershipStatus.INVITED.value

    def __str__(self):
        return self.email


class EnrollmentRecordQuerySet(models.QuerySet):
    """Custom QuerySet for EnrollmentRecord models."""

    def active(self):
        return self.filter(is_active=True)


class EnrollmentRecord(TimeStampedModel):
    """A record of a learner's enrollment in a partner offering."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="enrollment_records",
        on_delete=models.CASCADE,
    )
    offering = models.ForeignKey(
        PartnerOffering, related_name="enrollment_records", on_delete=models.CASCADE
    )
    mode = models.CharField(max_length=64)
    grade = models.PositiveSmallIntegerField(default=0)
    progress = models.PositiveSmallIntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    is_successful = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    creation_date = models.DateTimeField(default=timezone.now)

    objects = EnrollmentRecordQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "offering"], name="unique_user_per_offering"
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.offering} - active: {self.is_active}"
