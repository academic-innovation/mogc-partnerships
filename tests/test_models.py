import pytest

from mogc_partnerships import factories


@pytest.mark.django_db
class TestPartner:
    def test_str(self):
        partner = factories.PartnerFactory(name="Gizmonic Institute")
        assert str(partner) == "Gizmonic Institute"


@pytest.mark.django_db
class TestEnrollmentRecord:
    """Tests for the EnrollmentRecord model."""

    def test_str(self):
        record = factories.EnrollmentRecordFactory(
            user__username="username",
            offering__course_key="course-v1:edX+DemoX+Demo_Course",
            offering__partner__name="Partner",
        )
        assert str(record) == "username in course-v1:edX+DemoX+Demo_Course [Partner]"
