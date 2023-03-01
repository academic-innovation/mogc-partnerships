import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from mogc_partnerships import factories, views
from mogc_partnerships.models import PartnerCatalog


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
        memberships = factories.CatalogMembershipFactory.create_batch(2, user=user)
        for membership in memberships:
            factories.PartnerOfferingFactory(partner=membership.catalog.partner)
        request = api_rf.get("/partners/")
        force_authenticate(request, user=user)
        partner_list_view = views.PartnerListView.as_view()

        response = partner_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 2
        for partner in other_partners:
            assert partner.slug not in [item["slug"] for item in response.data]
        for membership in memberships:
            partner = membership.catalog.partner
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
class TestCatalogListView:
    """Tests for CatalogListView."""

    def test_manager_can_list_catalogs(self, api_rf):
        """A partnership manager can list catalogs for the partner."""

        user = factories.UserFactory()
        management_association = factories.PartnerManagementMembershipFactory(user=user)
        factories.PartnerCatalogFactory.create_batch(
            3, partner=management_association.partner
        )
        other_catalog = factories.PartnerCatalogFactory()
        catalog_list_view = views.CatalogListView.as_view()
        request = api_rf.get("/catalogs/")
        force_authenticate(request, user=user)

        response = catalog_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 3
        assert other_catalog.uuid not in [item["uuid"] for item in response.data]

    def test_learner_list_empty(self, api_rf):
        """Learners should not see catalogs listed."""

        user = factories.UserFactory()
        factories.CatalogMembershipFactory(user=user)
        catalog_list_view = views.CatalogListView.as_view()
        request = api_rf.get("/catalogs/")
        force_authenticate(request, user=user)

        response = catalog_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_manager_can_create_catalog(self, api_rf):
        """A manager can create catalogs for partners that they manage."""

        user = factories.UserFactory()
        management_association = factories.PartnerManagementMembershipFactory(user=user)
        partner = management_association.partner
        catalog_list_view = views.CatalogListView.as_view()
        request = api_rf.post(
            "/catalogs/",
            {"partner": partner.slug, "name": "A new catalog"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = catalog_list_view(request)

        assert response.status_code == 201
        assert response.data["partner"] == partner.slug
        assert response.data["name"] == "A new catalog"
        assert partner.catalogs.filter(uuid=response.data["uuid"]).count() == 1

    def test_learner_can_not_create_catalog(self, api_rf):
        """Catalogs can not be created by learners."""

        user = factories.UserFactory()
        membership = factories.CatalogMembershipFactory(user=user)
        partner = membership.catalog.partner
        catalog_list_view = views.CatalogListView.as_view()
        request = api_rf.post(
            "/catalogs/",
            {"partner": partner.slug, "name": "A new catalog"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = catalog_list_view(request)

        assert response.status_code == 403

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        partner = factories.PartnerFactory()
        catalog_list_view = views.CatalogListView.as_view()
        request = api_rf.post(
            "/catalogs/",
            {"partner": partner.slug, "name": "A new catalog"},
            format="json",
        )

        response = catalog_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCatalogDetailView:
    """Tests for CatalogDetailView."""

    def test_manager_can_update_own_catalog(self, api_rf):
        """Manager may update existing catalogs."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        request = api_rf.put(
            f"/catalog/{catalog.uuid}/", {"name": "New catalog name"}, format="json"
        )
        force_authenticate(request, manager.user)
        catalog_detail_view = views.CatalogDetailView.as_view()

        response = catalog_detail_view(request, uuid=catalog.uuid)
        catalog.refresh_from_db()

        assert response.status_code == 200
        assert catalog.name == "New catalog name"

    def test_only_manager_can_update_catalog(self, api_rf):
        """Only managers may update existing catalogs."""

        user = factories.UserFactory()
        catalog = factories.PartnerCatalogFactory()
        request = api_rf.put(
            f"/catalog/{catalog.uuid}/", {"name": "New catalog name"}, format="json"
        )
        force_authenticate(request, user)
        catalog_detail_view = views.CatalogDetailView.as_view()

        response = catalog_detail_view(request, uuid=catalog.uuid)

        assert response.status_code == 404

    def test_catalog_partner_does_not_change(self, api_rf):
        """Catalogs may not be moved to a different partner."""

        user = factories.UserFactory()
        manager = factories.PartnerManagementMembershipFactory(user=user)
        other_manager = factories.PartnerManagementMembershipFactory(user=user)
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        request = api_rf.put(
            f"/catalog/{catalog.uuid}/",
            {"partner": other_manager.partner.slug, "name": "New catalog name"},
            format="json",
        )
        force_authenticate(request, user)
        catalog_detail_view = views.CatalogDetailView.as_view()

        response = catalog_detail_view(request, uuid=catalog.uuid)
        catalog.refresh_from_db()

        assert response.status_code == 200
        assert catalog.partner != other_manager.partner.slug
        assert catalog.name == "New catalog name"

    def test_manager_can_delete_catalog(self, api_rf):
        """Managera may delete existing catalogs."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        request = api_rf.delete(f"/catalog/{catalog.uuid}/", format="json")
        force_authenticate(request, manager.user)
        catalog_detail_view = views.CatalogDetailView.as_view()

        response = catalog_detail_view(request, uuid=catalog.uuid)

        assert response.status_code == 204
        assert not PartnerCatalog.objects.filter(uuid=catalog.uuid).exists()

    def test_only_manager_can_delete_catalog(self, api_rf):
        """Only managers may delete existing catalogs."""

        user = factories.UserFactory()
        catalog = factories.PartnerCatalogFactory()
        request = api_rf.delete(f"/catalog/{catalog.uuid}/", format="json")
        force_authenticate(request, user)
        catalog_detail_view = views.CatalogDetailView.as_view()

        response = catalog_detail_view(request, uuid=catalog.uuid)

        assert response.status_code == 404

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        catalog = factories.PartnerCatalogFactory()
        catalog_detail_view = views.CatalogDetailView.as_view()
        request = api_rf.get(f"/catalogs/{catalog.uuid}/")

        response = catalog_detail_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCatalogOfferingListView:
    """Tests for CatalogOfferingListView."""

    def test_managed_offerings_listed(self, api_rf):
        """Managers should see offerings for all catalogs they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CatalogOfferingFactory(catalog__partner=manager.partner)
        offering_list_view = views.CatalogOfferingListView.as_view()
        request = request = api_rf.get("/offerings/")
        force_authenticate(request, manager.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_unmanaged_offerings_not_listed(self, api_rf):
        """Managers shouldn't see offerings for catalogs they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CatalogOfferingFactory()
        offering_list_view = views.CatalogOfferingListView.as_view()
        request = request = api_rf.get("/offerings/")
        force_authenticate(request, manager.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_membership_offerings_listed(self, api_rf):
        """Members should see offerings for their catalogs."""

        member = factories.CatalogMembershipFactory()
        factories.CatalogOfferingFactory(catalog=member.catalog)
        offering_list_view = views.CatalogOfferingListView.as_view()
        request = request = api_rf.get("/offerings/")
        force_authenticate(request, member.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_other_offerings_not_listed(self, api_rf):
        """Members shouldn't see offerings from catalogs if they aren't a member."""

        member = factories.CatalogMembershipFactory()
        factories.CatalogOfferingFactory()
        offering_list_view = views.CatalogOfferingListView.as_view()
        request = request = api_rf.get("/offerings/")
        force_authenticate(request, member.user)

        response = offering_list_view(request)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        offering_list_view = views.CatalogOfferingListView.as_view()
        request = api_rf.get("/offerings/")

        response = offering_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCatalogOfferingCreateView:
    """Tests for CatalogOfferingCreateView."""

    def test_manager_can_add_offering(self, api_rf):
        """Managers can add offerings to catalogs they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        offering = factories.PartnerOfferingFactory(partner=manager.partner)
        offering_create_view = views.CatalogOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{catalog.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, catalog_uuid=catalog.uuid)

        assert response.status_code == 201
        assert catalog.offerings.first().offering == offering

    def test_only_own_catalog(self, api_rf):
        """Managers can't add offerings to catalogs that they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory()
        offering = factories.PartnerOfferingFactory(partner=manager.partner)
        offering_create_view = views.CatalogOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{catalog.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, catalog_uuid=catalog.uuid)

        assert response.status_code == 403
        assert not catalog.offerings.exists()

    def test_only_add_available_courses(self, api_rf):
        """Managers can't add offerings from partners that they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        offering = factories.PartnerOfferingFactory()
        offering_create_view = views.CatalogOfferingCreateView.as_view()
        request = api_rf.post(f"/offerings/{catalog.uuid}/", {"offering": offering.id})
        force_authenticate(request, manager.user)

        response = offering_create_view(request, catalog_uuid=catalog.uuid)

        assert response.status_code == 403
        assert not catalog.offerings.exists()

    def test_anonymous_user_forbidden(self, api_rf):
        """Anonymous users should receive status 403."""

        catalog = factories.PartnerCatalogFactory()
        partner_offering = factories.PartnerOfferingFactory(partner=catalog.partner)
        offering_create_view = views.CatalogOfferingListView.as_view()
        request = api_rf.post(
            f"/offerings/{catalog.uuid}", {"offering": partner_offering}
        )

        response = offering_create_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestCatalogMembershipListView:
    """Tests for CatalogMembershipListView."""

    def test_managers_see_own_memberships(self, api_rf):
        """Managers should see memberships for catalogs they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CatalogMembershipFactory(catalog__partner=manager.partner)
        membership_list_view = views.CatalogMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)

        response = membership_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 1

    def test_unmanaged_memberships_not_listed(self, api_rf):
        """Managers shouldn't see memberships for catalogs they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CatalogMembershipFactory()
        membership_list_view = views.CatalogMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)

        response = membership_list_view(request)

        assert response.status_code == 200
        assert len(response.data["results"]) == 0

    @pytest.mark.parametrize(("objs", "queries"), [(3, 2), (7, 2)])
    def test_query_count(self, api_rf, django_assert_num_queries, objs, queries):
        """Managers should see memberships for catalogs they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        factories.CatalogMembershipFactory.create_batch(
            objs, catalog__partner=manager.partner
        )
        membership_list_view = views.CatalogMembershipListView.as_view()
        request = api_rf.get("/memberships/")
        force_authenticate(request, manager.user)
        with django_assert_num_queries(queries):
            response = membership_list_view(request)

        assert response.status_code == 200


@pytest.mark.django_db
class TestCatalogMembershipCreateView:
    """Tests for CatalogMembershipCreateView."""

    def test_manager_can_create_membership(self, api_rf):
        """Managers can create membership for catalogs they manage."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory(partner=manager.partner)
        member_create_view = views.CatalogMembershipCreateView.as_view()
        request = api_rf.post(f"/memberships/{catalog.uuid}/", {"email": "a@b.com"})
        force_authenticate(request, manager.user)

        response = member_create_view(request, catalog_uuid=catalog.uuid)

        assert response.status_code == 201
        assert catalog.memberships.first().email == "a@b.com"

    def test_only_own_catalog(self, api_rf):
        """Managers can't create memberships for catalogs they don't manage."""

        manager = factories.PartnerManagementMembershipFactory()
        catalog = factories.PartnerCatalogFactory()
        member_create_view = views.CatalogMembershipCreateView.as_view()
        request = api_rf.post(f"/memberships/{catalog.uuid}/", {"email": "a@b.com"})
        force_authenticate(request, manager.user)

        response = member_create_view(request, catalog_uuid=catalog.uuid)

        assert response.status_code == 403
        assert not catalog.memberships.exists()


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
