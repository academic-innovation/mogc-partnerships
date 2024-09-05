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
        f"{API_PREFIX}/cohorts/",
        views.CohortListView.as_view(),
        name="cohort_list",
    ),
    path(
        f"{API_PREFIX}/cohorts/<uuid:uuid>",
        views.CohortDetailView.as_view(),
        name="cohort_detail",
    ),
    path(
        f"{API_PREFIX}/offerings/",
        views.CohortOfferingListView.as_view(),
        name="offering_list",
    ),
    path(
        f"{API_PREFIX}/offerings/<uuid:cohort_uuid>/",
        views.CohortOfferingCreateView.as_view(),
        name="offering_create",
    ),
    path(
        f"{API_PREFIX}/offerings/<int:offering_id>/enroll/",
        views.enroll_member,
        name="enroll_member",
    ),
    path(
        f"{API_PREFIX}/memberships/",
        views.CohortMembershipListView.as_view(),
        name="membership_list",
    ),
    path(
        f"{API_PREFIX}/memberships/<uuid:cohort_uuid>/",
        views.CohortMembershipCreateView.as_view(),
        name="membership_create",
    ),
    path(
        f"{API_PREFIX}/memberships/<uuid:cohort_uuid>/<int:pk>/",
        views.CohortMembershipUpdateView.as_view(),
        name="membership_update",
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
