import logging

from celery import shared_task
from opaque_keys.edx.keys import CourseKey

from .compat import get_course_overview_or_none
from .models import Partner, PartnerOffering

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
