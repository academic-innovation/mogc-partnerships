import logging

from celery import shared_task
from opaque_keys.edx.keys import CourseKey

from .compat import get_course_overview_or_none
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
def trigger_send_cohort_membership_invite(cohort_membership_id):
    cohort_membership = CohortMembership.objects.get(pk=cohort_membership_id)
    send_cohort_membership_invite(cohort_membership)


@shared_task
def trigger_send_cohort_membership_invites(cohort_membership_ids):
    cohort_memberships = CohortMembership.objects.filter(pk__in=cohort_membership_ids).all()
    for member in cohort_memberships:
        send_cohort_membership_invite(member)
