import json

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from mogc_partnerships import enums, factories, views
from mogc_partnerships.models import PartnerCohort


@pytest.fixture
def api_rf():
    return APIRequestFactory()


@pytest.mark.django_db
class TestPartnerListView:
    """Tests for PartnerListView."""

    def test_managed_partners_are_listed(self, api_rf):
        """Partners managed by the user should be returned with offerings."""

        user = factories.UserFactory()
        partners = factories.PartnerFactory.create_batch(3)
        associations = factories.PartnerManagementMembershipFactory.create_batch(
            2, user=user
        )
        for association in associations:
            factories.PartnerOfferingFactory(partner=association.partner)
        partner_list_view = views.PartnerListView.as_view()
        request = api_rf.get("/partners/")
        force_authenticate(request, user=user)

        response = partner_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 2
        for partner in partners:
            assert partner.slug not in [item["slug"] for item in response.data]
        for association in associations:
            assert association.partner.slug in [item["slug"] for item in response.data]
        for item in response.data:
            assert len(item["offerings"]) > 0

    def test_learner_partners_are_listed(self, api_rf):
        """Learners should receive partners without offerings."""

        user = factories.UserFactory()
        other_partners = factories.PartnerFactory.create_batch(3)
        memberships = factories.CohortMembershipFactory.create_batch(2, user=user)
        for membership in memberships:
            factories.PartnerOfferingFactory(partner=membership.cohort.partner)
        request = api_rf.get("/partners/")
        force_authenticate(request, user=user)
        partner_list_view = views.PartnerListView.as_view()

        response = partner_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 2
        for partner in other_partners:
            assert partner.slug not in [item["slug"] for item in response.data]
        for membership in memberships:
            partner = membership.cohort.partner
            assert partner.slug in [item["slug"] for item in response.data]
        for item in response.data:
            assert len(item["offerings"]) == 0

    def test_anonymous_forbidden(self, api_rf):
        """Anonymous users should receive 403 forbidden."""

        factories.PartnerManagementMembershipFactory.create_batch(2)
        partner_list_view = views.PartnerListView.as_view()
        request = api_rf.get("/partners/")

        response = partner_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCohortListView:
    """Tests for CohortListView."""

    def test_manager_can_list_cohorts(self, api_rf):
        """A partnership manager can list cohorts for the partner."""

        user = factories.UserFactory()
        management_association = factories.PartnerManagementMembershipFactory(user=user)
        factories.PartnerCohortFactory.create_batch(
            3, partner=management_association.partner
        )
        other_cohort = factories.PartnerCohortFactory()
        cohort_list_view = views.CohortListView.as_view()
        request = api_rf.get("/cohorts/")
        force_authenticate(request, user=user)

        response = cohort_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 3
        assert other_cohort.uuid not in [item["uuid"] for item in response.data]

    def test_learner_list_empty(self, api_rf):
        """Learners should not see cohorts listed."""

        user = factories.UserFactory()
        factories.CohortMembershipFactory(user=user)
        cohort_list_view = views.CohortListView.as_view()
        request = api_rf.get("/cohorts/")
        force_authenticate(request, user=user)

        response = cohort_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_manager_can_create_cohort(self, api_rf):
        """A manager can create cohorts for partners that they manage."""

        user = factories.UserFactory()
        management_association = factories.PartnerManagementMembershipFactory(user=user)
        partner = management_association.partner
        cohort_list_view = views.CohortListView.as_view()
        request = api_rf.post(
            "/cohorts/",
            {"partner": partner.slug, "name": "A new cohort"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = cohort_list_view(request)

        assert response.status_code == 201
        assert response.data["partner"] == partner.slug
        assert response.data["name"] == "A new cohort"
        assert partner.cohorts.filter(uuid=response.data["uuid"]).count() == 1

    def test_learner_can_not_create_cohort(self, api_rf):
        """Cohorts can not be created by learners."""

        user = factories.UserFactory()
        membership = factories.CohortMembershipFactory(user=user)
        partner = membership.cohort.partner
        cohort_list_view = views.CohortListView.as_view()
        request = api_rf.post(
            "/cohorts/",
            {"partner": partner.slug, "name": "A new cohort"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = cohort_list_view(request)

        assert response.status_code == 403

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        partner = factories.PartnerFactory()
        cohort_list_view = views.CohortListView.as_view()
        request = api_rf.post(
            "/cohorts/",
            {"partner": partner.slug, "name": "A new cohort"},
            format="json",
        )

        response = cohort_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCohortDetailView:
    """Tests for CohortDetailView."""

    def test_manager_can_update_own_cohort(self, api_rf):
        """Manager may update existing cohorts."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        request = api_rf.put(
            f"/cohort/{cohort.uuid}/", {"name": "New cohort name"}, format="json"
        )
        force_authenticate(request, manager.user)
        cohort_detail_view = views.CohortDetailView.as_view()

        response = cohort_detail_view(request, uuid=cohort.uuid)
        cohort.refresh_from_db()

        assert response.status_code == 200
        assert cohort.name == "New cohort name"

    def test_only_manager_can_update_cohort(self, api_rf):
        """Only managers may update existing cohorts."""

        user = factories.UserFactory()
        cohort = factories.PartnerCohortFactory()
        request = api_rf.put(
            f"/cohort/{cohort.uuid}/", {"name": "New cohort name"}, format="json"
        )
        force_authenticate(request, user)
        cohort_detail_view = views.CohortDetailView.as_view()

        response = cohort_detail_view(request, uuid=cohort.uuid)

        assert response.status_code == 404

    def test_cohort_partner_does_not_change(self, api_rf):
        """Cohorts may not be moved to a different partner."""

        user = factories.UserFactory()
        manager = factories.PartnerManagementMembershipFactory(user=user)
        other_manager = factories.PartnerManagementMembershipFactory(user=user)
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        request = api_rf.put(
            f"/cohort/{cohort.uuid}/",
            {"partner": other_manager.partner.slug, "name": "New cohort name"},
            format="json",
        )
        force_authenticate(request, user)
        cohort_detail_view = views.CohortDetailView.as_view()

        response = cohort_detail_view(request, uuid=cohort.uuid)
        cohort.refresh_from_db()

        assert response.status_code == 200
        assert cohort.partner != other_manager.partner.slug
        assert cohort.name == "New cohort name"

    def test_manager_can_delete_cohort(self, api_rf):
        """Managera may delete existing cohorts."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        request = api_rf.delete(f"/cohort/{cohort.uuid}/", format="json")
        force_authenticate(request, manager.user)
        cohort_detail_view = views.CohortDetailView.as_view()

        response = cohort_detail_view(request, uuid=cohort.uuid)

        assert response.status_code == 204
        assert not PartnerCohort.objects.filter(uuid=cohort.uuid).exists()

    def test_only_manager_can_delete_cohort(self, api_rf):
        """Only managers may delete existing cohorts."""

        user = factories.UserFactory()
        cohort = factories.PartnerCohortFactory()
        request = api_rf.delete(f"/cohort/{cohort.uuid}/", format="json")
        force_authenticate(request, user)
        cohort_detail_view = views.CohortDetailView.as_view()

        response = cohort_detail_view(request, uuid=cohort.uuid)

        assert response.status_code == 404

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        cohort = factories.PartnerCohortFactory()
        cohort_detail_view = views.CohortDetailView.as_view()
        request = api_rf.get(f"/cohorts/{cohort.uuid}/")

        response = cohort_detail_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCohortOfferingListView:
    """Tests for CohortOfferingListView."""

    def test_managed_offerings_listed(self, api_rf):
        """Managers should see offerings for all cohorts they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CohortOfferingFactory(cohort__partner=manager.partner)
        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")
        force_authenticate(request, manager.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_unmanaged_offerings_not_listed(self, api_rf):
        """Managers shouldn't see offerings for cohorts they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CohortOfferingFactory()
        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")
        force_authenticate(request, manager.user)

        response = offering_list_view(request)

        assert response.status_code == 403

    def test_membership_offerings_listed(self, api_rf):
        """Members should see offerings for their cohorts."""

        member = factories.CohortMembershipFactory()
        factories.CohortOfferingFactory(cohort=member.cohort)
        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")
        force_authenticate(request, member.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_deactivated_membership_offerings_not_listed(self, api_rf):
        """Members shouldn't see offerings if they are deactivated."""

        member = factories.CohortMembershipFactory(active=False)
        factories.CohortOfferingFactory(cohort=member.cohort)
        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")
        force_authenticate(request, member.user)

        response = offering_list_view(request)

        assert response.status_code == 403

    def test_other_offerings_not_listed(self, api_rf):
        """Members shouldn't see offerings from cohorts if they aren't a member."""

        member = factories.CohortMembershipFactory()
        factories.CohortOfferingFactory()
        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")
        force_authenticate(request, member.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        offering_list_view = views.CohortOfferingListView.as_view()
        request = api_rf.get("/offerings/")

        response = offering_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCohortOfferingCreateView:
    """Tests for CohortOfferingCreateView."""

    def test_manager_can_add_offering(self, api_rf):
        """Managers can add offerings to cohorts they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        offering = factories.PartnerOfferingFactory(partner=manager.partner)
        offering_create_view = views.CohortOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{cohort.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 201
        assert cohort.offerings.first().offering == offering

    def test_only_own_cohort(self, api_rf):
        """Managers can't add offerings to cohorts that they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory()
        offering = factories.PartnerOfferingFactory(partner=manager.partner)
        offering_create_view = views.CohortOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{cohort.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 403
        assert not cohort.offerings.exists()

    def test_only_add_available_courses(self, api_rf):
        """Managers can't add offerings from partners that they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        offering = factories.PartnerOfferingFactory()
        offering_create_view = views.CohortOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{cohort.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 403
        assert not cohort.offerings.exists()

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        cohort = factories.PartnerCohortFactory()
        partner_offering = factories.PartnerOfferingFactory(partner=cohort.partner)
        offering_create_view = views.CohortOfferingListView.as_view()
        request = api_rf.post(
            f"/offerings/{cohort.uuid}", {"offering": partner_offering}
        )

        response = offering_create_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCohortMembershipListView:
    """Tests for CohortMembershipListView."""

    def test_managers_see_own_memberships(self, api_rf):
        """Managers should see memberships for cohorts they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CohortMembershipFactory(cohort__partner=manager.partner)
        membership_list_view = views.CohortMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)

        response = membership_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_unmanaged_memberships_not_listed(self, api_rf):
        """Managers shouldn't see memberships for cohorts they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CohortMembershipFactory()
        membership_list_view = views.CohortMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)

        response = membership_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 0

    @pytest.mark.parametrize(("objs", "queries"), [(3, 2), (7, 2)])
    def test_query_count(self, api_rf, django_assert_num_queries, objs, queries):
        """Managers should see memberships for cohorts they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CohortMembershipFactory.create_batch(
            objs, cohort__partner=manager.partner
        )
        membership_list_view = views.CohortMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)
        with django_assert_num_queries(queries):
            response = membership_list_view(request)

        assert response.status_code == 200


@pytest.mark.django_db
class TestCohortMembershipCreateView:
    """Tests for CohortMembershipCreateView."""

    def test_manager_can_create_membership(self, api_rf, mocker):
        """Managers can create membership for cohorts they manage."""
        mock_message_task = mocker.patch(
            "mogc_partnerships.tasks.trigger_send_cohort_membership_invite.delay"
        )

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        member_create_view = views.CohortMembershipCreateView.as_view()
        request = api_rf.post(f"/memberships/{cohort.uuid}/", {"email": "a@b.com"})
        force_authenticate(request, manager.user)

        response = member_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 201
        assert cohort.memberships.first().email == "a@b.com"
        # TODO: Revert when email reenabled
        # assert mock_message_task.call_count == 1
        assert mock_message_task.call_count == 0

    def test_only_own_cohort(self, api_rf):
        """Managers can't create memberships for cohorts they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory()
        member_create_view = views.CohortMembershipCreateView.as_view()
        request = api_rf.post(f"/memberships/{cohort.uuid}/", {"email": "a@b.com"})
        force_authenticate(request, manager.user)

        response = member_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 403
        assert not cohort.memberships.exists()

    def test_bulk_create(self, api_rf, mocker):
        """Managers can upload a list of emails to bulk create memberships"""
        mock_message_task = mocker.patch(
            "mogc_partnerships.tasks.trigger_send_cohort_membership_invites.delay"
        )

        manager = factories.PartnerManagementMembershipFactory()
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        member_create_view = views.CohortMembershipCreateView.as_view()
        user_data = [{"email": "test-{}@test.com".format(i)} for i in range(10)]

        request = api_rf.post(
            f"/memberships/{cohort.uuid}/",
            json.dumps(user_data),
            content_type="application/json",
        )
        force_authenticate(request, manager.user)

        response = member_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 201
        assert len(response.data) == 10
        # TODO: Revert when email reenabled
        # assert mock_message_task.call_count == 1
        assert mock_message_task.call_count == 0

    def test_bulk_create_with_existing_user(self, api_rf, mocker):
        """
        Managers can upload a list of emails to bulk create memberships
        for existing user emails
        """
        mock_message_task = mocker.patch(
            "mogc_partnerships.tasks.trigger_send_cohort_membership_invites.delay"
        )

        manager = factories.PartnerManagementMembershipFactory()
        factories.UserFactory(email="foo@bar.com")
        cohort = factories.PartnerCohortFactory(partner=manager.partner)
        member_create_view = views.CohortMembershipCreateView.as_view()
        user_data = [{"email": "foo@bar.com"}]

        request = api_rf.post(
            f"/memberships/{cohort.uuid}/",
            json.dumps(user_data),
            content_type="application/json",
        )
        force_authenticate(request, manager.user)

        response = member_create_view(request, cohort_uuid=cohort.uuid)

        assert response.status_code == 201
        assert len(response.data) == 1
        # TODO: Revert when email reenabled
        # assert mock_message_task.call_count == 1
        assert mock_message_task.call_count == 0


@pytest.mark.django_db
class TestCohortMembershipUpdateView:
    """Tests for CohortMembershipUpdateView."""

    def _setup_enrollments(self):
        self.partner_offering = factories.PartnerOfferingFactory(partner=self.partner)
        self.cohort_offering = factories.CohortOfferingFactory(
            cohort=self.cohort, offering=self.partner_offering
        )
        self.enrollment_records = [
            factories.EnrollmentRecordFactory(
                user=self.user,
                offering=self.partner_offering,
                is_active=True,
            )
        ]
        self.user.enrollment_records.set(self.enrollment_records)

    def _make_request(self, api_rf, payload=None):
        request = api_rf.patch(
            f"/memberships/{self.cohort.uuid}/{self.membership.id}/",
            payload,
            format="json",
        )
        force_authenticate(request, self.manager.user)
        return self.member_update_view(
            request, cohort_uuid=self.cohort.uuid, pk=self.membership.id
        )

    def _setup(self, with_enrollments=False):
        self.user = factories.UserFactory()
        self.manager = factories.PartnerManagementMembershipFactory()

        self.partner = self.manager.partner
        self.cohort = factories.PartnerCohortFactory(partner=self.partner)
        self.membership = factories.CohortMembershipFactory(
            cohort=self.cohort, user=self.user
        )

        if with_enrollments:
            self._setup_enrollments()

        self.member_update_view = views.CohortMembershipUpdateView.as_view()

    def test_manager_can_update_membership(self, api_rf):
        """Managers can update membership for cohorts they manage."""
        self._setup()

        response = self._make_request(api_rf, payload={"active": False})
        assert response.status_code == 200
        assert (
            self.cohort.memberships.first().status
            == enums.CohortMembershipStatus.DEACTIVATED.value
        )

    def test_course_enrollments_deactivated_on_status_change(self, api_rf, mocker):
        """
        Confirms enrollment is marked inactive when a user is deactivated.
        """
        self._setup(with_enrollments=True)

        mocker.patch(
            "mogc_partnerships.compat.update_student_enrollment",
            return_value={
                "course_id": self.partner_offering.course_key,
                "course_home_url": "foo.com/bar",
                "enrolled": False,
            },
        )

        response = self._make_request(api_rf, payload={"active": False})
        self.enrollment_records[0].refresh_from_db()
        assert (
            self.cohort.memberships.first().status
            == enums.CohortMembershipStatus.DEACTIVATED.value
        )
        assert response.status_code == 200
        assert self.enrollment_records[0].is_active is False

    def test_course_enrollments_if_multiple_cohorts(self, api_rf):
        """
        Confirms enrollments are not affected if a user is a member of multiple
        cohorts with the same cohort offering.
        """
        self._setup(with_enrollments=True)

        # Create new cohort with existing offering in another cohort
        other_cohort = factories.PartnerCohortFactory(partner=self.manager.partner)
        factories.CohortMembershipFactory(cohort=other_cohort, user=self.user)
        factories.CohortOfferingFactory(
            cohort=other_cohort, offering=self.partner_offering
        )

        response = self._make_request(api_rf, payload={"active": False})
        self.enrollment_records[0].refresh_from_db()
        assert (
            self.cohort.memberships.first().status
            == enums.CohortMembershipStatus.DEACTIVATED.value
        )
        assert response.status_code == 200
        assert self.enrollment_records[0].is_active is True


@pytest.mark.django_db
class TestEnrollmentRecordListView:
    """Tests for EnrollmentRecordListView."""

    def test_managers_see_own_records(self, api_rf):
        manager = factories.PartnerManagementMembershipFactory()
        factories.EnrollmentRecordFactory(offering__partner=manager.partner)
        record_list_view = views.EnrollmentRecordListView.as_view()
        request = api_rf.get("/records/")
        force_authenticate(request, manager.user)

        response = record_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_unmanaged_records_not_listed(self, api_rf):
        manager = factories.PartnerManagementMembershipFactory()
        factories.EnrollmentRecordFactory()
        record_list_view = views.EnrollmentRecordListView.as_view()
        request = api_rf.get("/records/")
        force_authenticate(request, manager.user)

        response = record_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 0

    @pytest.mark.parametrize(("objs", "queries"), [(3, 2), (7, 2)])
    def test_query_count(self, api_rf, django_assert_num_queries, objs, queries):
        manager = factories.PartnerManagementMembershipFactory()
        factories.EnrollmentRecordFactory.create_batch(
            objs, offering__partner=manager.partner
        )
        record_list_view = views.EnrollmentRecordListView.as_view()
        request = api_rf.get("/records/")
        force_authenticate(request, manager.user)

        with django_assert_num_queries(queries):
            response = record_list_view(request)

        assert response.status_code == 200
