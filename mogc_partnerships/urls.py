from django.urls import path

from . import views

app_name = "mogc_partnershps"

API_PREFIX = "partnerships/v0"

urlpatterns = [
    path(
        f"{API_PREFIX}/partners/",
        views.PartnerListView.as_view(),
        name="partner_list",
    ),
    path(
        f"{API_PREFIX}/catalogs/",
        views.CatalogListView.as_view(),
        name="catalog_list",
    ),
    path(
        f"{API_PREFIX}/catalogs/<uuid:uuid>",
        views.CatalogDetailView.as_view(),
        name="catalog_detail",
    ),
    path(
        f"{API_PREFIX}/offerings/",
        views.CatalogOfferingListView.as_view(),
        name="offering_list",
    ),
    path(
        f"{API_PREFIX}/offerings/<uuid:catalog_uuid>/",
        views.CatalogOfferingCreateView.as_view(),
        name="offering_create",
    ),
    path(
        f"{API_PREFIX}/offerings/<int:offering_id>/enroll/",
        views.enroll_member,
        name="enroll_member",
    ),
    path(
        f"{API_PREFIX}/memberships/",
        views.CatalogMembershipListView.as_view(),
        name="membership_list",
    ),
    path(
        f"{API_PREFIX}/memberships/<uuid:catalog_uuid>/",
        views.CatalogMembershipCreateView.as_view(),
        name="membership_create",
    ),
    path(
        f"{API_PREFIX}/continue/<int:offering_id>/",  # TODO: Fix this yucky URL
        views.continue_learning,
        name="continue_learning",
    ),
    path(
        f"{API_PREFIX}/records/",
        views.EnrollmentRecordListView.as_view(),
        name="record_list",
    ),
]
