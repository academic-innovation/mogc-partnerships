import logging

from django.contrib.auth import get_user_model

from celery import shared_task
from opaque_keys.edx.keys import CourseKey

from . import tasks
from .compat import get_course_overview_or_none
from .exceptions import CohortMembershipImportError
from .messages import send_cohort_membership_invite
from .models import CohortMembership, Partner, PartnerOffering

logger = logging.getLogger(__name__)


@shared_task
def update_or_create_offering(course_id):
    course_key = CourseKey.from_string(course_id)
    try:
        partner = Partner.objects.get(org=course_key.org)
        course_overview = get_course_overview_or_none(course_id)
        if course_overview is not None:
            PartnerOffering.objects.update_or_create(
                partner=partner,
                course_key=course_key,
                defaults={
                    "title": course_overview.display_name,
                    "short_description": course_overview.short_description or "",
                },
            )
    except Partner.DoesNotExist:
        logger.debug(f"Offering not created for {course_key}")


@shared_task
def trigger_send_cohort_membership_invite(cohort_membership):
    send_cohort_membership_invite(cohort_membership)


@shared_task
def trigger_send_cohort_membership_invites(cohort_memberships):
    for member in cohort_memberships:
        send_cohort_membership_invite(member)


def batch_create_memberships(cohort, member_emails):
    try:
        User = get_user_model()
        membership_accounts = User.objects.filter(
            email__in=[email for email in member_emails]
        )
        account_email_map = {user.email: user for user in membership_accounts}

        cohort_memberships = [
            CohortMembership(
                user=account_email_map.get(member_email),
                cohort=cohort,
                email=member_email,
            )
            for member_email in member_emails
        ]

        objects = CohortMembership.objects.bulk_create(
            cohort_memberships, ignore_conflicts=True
        )
        # bulk_create doesn't return autoincremented IDs with MySQL DBs
        # so we have to query results separately
        cohort_memberships = CohortMembership.objects.filter(
            email__in=[cm.email for cm in objects], cohort=cohort
        )

        tasks.trigger_send_cohort_membership_invites(cohort_memberships)
    except Exception as e:
        raise CohortMembershipImportError(e)


@shared_task
def trigger_batch_create_memberships(cohort, member_emails):
    batch_create_memberships(cohort, member_emails)
