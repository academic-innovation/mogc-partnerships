from openedx_filters.filters import PipelineStep
from openedx_filters.learning.filters import CourseEnrollmentStarted

from .models import CatalogOffering, Partner, PartnerOffering


class MembershipRequiredEnrollment(PipelineStep):
    """Prevents non-members from enrolling in partner courses."""

    def run_filter(self, user, course_key, mode):
        try:
            partner = Partner.objects.get(org=course_key.org)
            offering = partner.offerings.get(course_key=course_key)
            catalog_ids = CatalogOffering.objects.filter(offering=offering).values_list(
                "id", flat=True
            )
            if user.memberships.filter(catalog__in=catalog_ids).exists():
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
