from dataclasses import dataclass

from django.contrib.auth.models import AnonymousUser
from django.http.response import Http404
from django.test import TestCase, override_settings

from crum import impersonate
from opaque_keys.edx.keys import CourseKey
from openedx_filters.learning.filters import (
    CourseAboutRenderStarted,
    CourseEnrollmentStarted,
)

from mogc_partnerships.factories import (
    CohortMembershipFactory,
    CohortOfferingFactory,
    PartnerManagementMembershipFactory,
    UserFactory,
)


@dataclass
class CourseDetails:
    """Stand-in for CourseDetails from edx-platform."""

    org: str
    course_id: str
    run: str

    @classmethod
    def from_course_key(cls, course_key):
        return cls(course_key.org, course_key.course, course_key.run)


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
        CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        with self.assertRaises(CourseEnrollmentStarted.PreventEnrollment):
            CourseEnrollmentStarted.run_filter(user, course_key, mode)

    def test_allows_member_enrollment(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        mode = "honor"
        offering = CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        CohortMembershipFactory(cohort=offering.cohort, email=user.email, user=user)
        result = CourseEnrollmentStarted.run_filter(user, course_key, mode)
        self.assertEqual(result, (user, course_key, mode))

    def test_allows_partner_staff_enrollment_without_cohort_membership(self):
        user = UserFactory(is_staff=True)
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        mode = "honor"
        offering = CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        PartnerManagementMembershipFactory(partner=offering.cohort.partner, user=user)
        result = CourseEnrollmentStarted.run_filter(user, course_key, mode)
        self.assertEqual(result, (user, course_key, mode))


@override_settings(
    OPEN_EDX_FILTERS_CONFIG={
        "org.openedx.learning.course_about.render.started.v1": {
            "fail_silently": False,
            "pipeline": ["mogc_partnerships.pipeline.HidePartnerCourseAboutPages"],
        }
    }
)
class TestHidePartnerCourseAboutPages(TestCase):
    """Tests for HidePartnerCourseAboutPages pipeline."""

    def test_displays_regular_courses(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        course_details = CourseDetails.from_course_key(course_key)
        context = {"course_details": course_details}
        template_name = "page_template.html"
        with impersonate(user):
            result = CourseAboutRenderStarted.run_filter(context, template_name)
        self.assertEqual(result, (context, template_name))

    def test_hides_partner_courses(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        course_details = CourseDetails.from_course_key(course_key)
        context = {"course_details": course_details}
        template_name = "page_template.html"
        with impersonate(user):
            with self.assertRaises(Http404):
                CourseAboutRenderStarted.run_filter(context, template_name)

    def test_hides_partner_courses_anon_user(self):
        user = AnonymousUser()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        course_details = CourseDetails.from_course_key(course_key)
        context = {"course_details": course_details}
        template_name = "page_template.html"
        with impersonate(user):
            with self.assertRaises(Http404):
                CourseAboutRenderStarted.run_filter(context, template_name)

    def test_displays_courses_to_members(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        offering = CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        CohortMembershipFactory(cohort=offering.cohort, email=user.email, user=user)
        course_details = CourseDetails.from_course_key(course_key)
        context = {"course_details": course_details}
        template_name = "page_template.html"
        with impersonate(user):
            result = CourseAboutRenderStarted.run_filter(context, template_name)
        self.assertEqual(result, (context, template_name))

    def test_displays_courses_to_partner_managers(self):
        user = UserFactory()
        course_key = CourseKey.from_string("course-v1:GizmonicInstitute+MST3K+S1_E1")
        offering = CohortOfferingFactory(
            cohort__partner__org=course_key.org, offering__course_key=course_key
        )
        PartnerManagementMembershipFactory(partner=offering.cohort.partner, user=user)
        course_details = CourseDetails.from_course_key(course_key)
        context = {"course_details": course_details}
        template_name = "page_template.html"
        with impersonate(user):
            result = CourseAboutRenderStarted.run_filter(context, template_name)
        self.assertEqual(result, (context, template_name))
