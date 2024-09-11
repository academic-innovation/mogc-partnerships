from django.http.response import Http404

from crum import get_current_user
from opaque_keys.edx.keys import CourseKey
from openedx_filters.filters import PipelineStep
from openedx_filters.learning.filters import CourseEnrollmentStarted

from .models import CohortOffering, Partner, PartnerOffering


def get_course_key(context):
    course_details = context["course_details"]
    org = course_details.org
    course_id = course_details.course_id
    run = course_details.run
    # TODO: Find a better way to do this.
    return CourseKey.from_string(
        "course-v1:" + "+".join([org, course_id, run])
    )

def user_can_access_course(user, partner, offering):
    if not user or user.is_anonymous:
        raise Http404
    cohort_ids = CohortOffering.objects.filter(offering=offering).values_list(
        "cohort_id", flat=True
    )
    cohort_membership = user.memberships.filter(cohort__in=cohort_ids)
    management_membership = user.management_memberships.filter(
        user_id=user.id, partner_id=partner.id
    )
    return cohort_membership.exists() or management_membership.exists()


class MembershipRequiredEnrollment(PipelineStep):
    """Prevents non-members from enrolling in partner courses."""

    def run_filter(self, user, course_key, mode):
        try:
            partner = Partner.objects.get(org=course_key.org)
            offering = partner.offerings.get(course_key=course_key)
            if user_can_access_course(user, partner, offering):
                return {}
            raise CourseEnrollmentStarted.PreventEnrollment(
                "This course requires a partner membership."
            )
        except PartnerOffering.DoesNotExist:
            raise CourseEnrollmentStarted.PreventEnrollment(
                "This course requires a partner membership."
            )
        except Partner.DoesNotExist:
            return {}


class HidePartnerCourseAboutPages(PipelineStep):
    """Return 404 to non-members for partner course about pages."""

    def run_filter(self, context, template_name):
        user = get_current_user()
        course_key = get_course_key(context)
        try:
            partner = Partner.objects.get(org=course_key.org)
            offering = partner.offerings.get(course_key=course_key)
            if user_can_access_course(user, partner, offering):
                return {}
            raise Http404
        except PartnerOffering.DoesNotExist:
            raise Http404
        except Partner.DoesNotExist:
            return {}
