from django.http.response import Http404

from crum import get_current_user
from opaque_keys.edx.keys import CourseKey
from openedx_filters.filters import PipelineStep
from openedx_filters.learning.filters import CourseEnrollmentStarted

from .models import CohortOffering, Partner, PartnerOffering


class MembershipRequiredEnrollment(PipelineStep):
    """Prevents non-members from enrolling in partner courses."""

    def run_filter(self, user, course_key, mode):
        try:
            partner = Partner.objects.get(org=course_key.org)
            offering = partner.offerings.get(course_key=course_key)
            cohort_ids = CohortOffering.objects.filter(offering=offering).values_list(
                "id", flat=True
            )
            if user.memberships.filter(cohort__in=cohort_ids).exists():
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
        print(context)
        course_details = context["course_details"]
        org = course_details.org
        course_id = course_details.course_id
        run = course_details.run
        course_key = CourseKey.from_string(
            "course-v1:" + "+".join([org, course_id, run])
        )  # TODO: Find a better way to do this.
        try:
            partner = Partner.objects.get(org=org)
            offering = partner.offerings.get(course_key=course_key)
            cohort_ids = CohortOffering.objects.filter(offering=offering).values_list(
                "id", flat=True
            )
            if user.memberships.filter(cohort__in=cohort_ids).exists():
                return {}
            raise Http404
        except PartnerOffering.DoesNotExist:
            raise Http404
        except Partner.DoesNotExist:
            return {}
