from django.test import TestCase, override_settings

from opaque_keys.edx.keys import CourseKey
from openedx_filters.learning.filters import CourseEnrollmentStarted

from mogc_partnerships.factories import (
    CatalogMembershipFactory,
    CatalogOfferingFactory,
    UserFactory,
)


@override_settings(
    OPEN_EDX_FILTERS_CONFIG={
        "org.openedx.learning.course.enrollment.started.v1": {
            "fail_silently": False,
            "pipeline": ["mogc_partnerships.pipeline.MembershipRequiredEnrollment"],
        }
    }
)
class TestMembershipRequiredEnrollment(TestCase):
    """Tests for MembershipRequiredEnrollment pipeline."""

    def test_allows_regular_enrollment(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        mode = "honor"
        result = CourseEnrollmentStarted.run_filter(user, course_key, mode)
        self.assertEqual(result, (user, course_key, mode))

    def test_prevents_partner_enrollment(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        mode = "honor"
        CatalogOfferingFactory(
            catalog__partner__org=course_key.org, offering__course_key=course_key
        )
        with self.assertRaises(CourseEnrollmentStarted.PreventEnrollment):
            CourseEnrollmentStarted.run_filter(user, course_key, mode)

    def test_allows_member_enrollment(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        mode = "honor"
        offering = CatalogOfferingFactory(
            catalog__partner__org=course_key.org, offering__course_key=course_key
        )
        CatalogMembershipFactory(catalog=offering.catalog, email=user.email, user=user)
        result = CourseEnrollmentStarted.run_filter(user, course_key, mode)
        self.assertEqual(result, (user, course_key, mode))
