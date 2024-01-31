from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mogc_partnerships import serializers

from . import compat
from .models import (
    CohortMembership,
    CohortOffering,
    EnrollmentRecord,
    Partner,
    PartnerCohort,
    PartnerManagementMembership,
    PartnerOffering,
)
from .pagination import LargeResultsSetPagination


class PartnerListView(APIView):
    """Returns a list of partners where the user is a member or manager."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        associations = PartnerManagementMembership.objects.filter(
            user=request.user
        ).values_list("partner_id", flat=True)
        partners = (
            Partner.objects.active()
            .for_user(request.user)
            .prefetch_related(
                Prefetch(
                    "offerings",
                    queryset=PartnerOffering.objects.filter(
                        partner_id__in=associations
                    ),
                ),
            )
        )
        serializer = serializers.PartnerSerializer(
            partners, many=True, context={"associations": associations}
        )
        return Response(serializer.data)


class CohortListView(generics.ListCreateAPIView):
    """List and create cohorts."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PartnerCohortSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        memberships = PartnerManagementMembership.objects.filter(user=user)
        return PartnerCohort.objects.filter(
            partner__in=memberships.values_list("partner_id", flat=True)
        )

    def perform_create(self, serializer):
        partner = serializer.validated_data["partner"]
        if self.request.user not in partner.managers.all():
            self.permission_denied(
                self.request, f"Cannot create cohort for {partner.slug}"
            )
        return super().perform_create(serializer)


class CohortDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Allows managers to update and delete cohorts for their partners."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PartnerCohortUpdateSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        user = self.request.user
        return PartnerCohort.objects.filter(
            partner__in=user.partners.values_list("id", flat=True)
        )


class CohortOfferingListView(generics.ListAPIView):
    """Lists cohort offerings."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CohortOfferingSerializer
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["enrollments"] = self.request.user.enrollment_records.values_list(
            "offering_id", flat=True
        )
        return context

    def get_queryset(self):
        user = self.request.user
        managed_partners = user.partners.all()
        managed_offerings = CohortOffering.objects.filter(
            cohort__partner_id__in=managed_partners.values_list("id", flat=True)
        )
        memberships = user.memberships.all()
        member_offerings = CohortOffering.objects.filter(
            cohort__in=memberships.values_list("cohort_id", flat=True)
        )
        accessible_offerings = managed_offerings | member_offerings
        return accessible_offerings.select_related("offering")


class CohortOfferingCreateView(generics.CreateAPIView):
    """Adds offerings to cohorts."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CohortOfferingSerializer

    def perform_create(self, serializer):
        user = self.request.user
        managed_cohorts = PartnerCohort.objects.filter(
            partner__in=user.partners.values_list("id", flat=True)
        )
        cohort_uuid = self.kwargs.get("cohort_uuid")
        try:
            cohort = managed_cohorts.get(uuid=cohort_uuid)
        except PartnerCohort.DoesNotExist:
            raise PermissionDenied("No")
        offering = serializer.validated_data["offering"]
        if offering not in cohort.partner.offerings.all():
            raise PermissionDenied("No!")
        serializer.save(cohort=cohort)


class CohortMembershipListView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CohortMembershipSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        managed_memberships = CohortMembership.objects.filter(
            cohort__partner__in=user.partners.values_list("id", flat=True)
        )

        # TODO: Find a better way to determine if profiles are present.
        # This allows us to avoid an N+1 issue in production while still passing tests.
        user_relationship = "user__profile" if hasattr(user, "profile") else "user"

        return managed_memberships.select_related("cohort__partner", user_relationship)


class CohortMembershipCreateView(generics.CreateAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CohortMembershipSerializer

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super(CohortMembershipCreateView, self).get_serializer(*args, **kwargs)

    def get_serializer_context(self):
        try:
            user = self.request.user
            managed_partners = Partner.objects.active().for_user(user)
            managed_cohorts = PartnerCohort.objects.filter(
                partner__in=managed_partners.values_list("id", flat=True)
            )
            cohort_uuid = self.kwargs.get("cohort_uuid")
            cohort = managed_cohorts.get(uuid=cohort_uuid)
        except PartnerCohort.DoesNotExist:
            raise PermissionDenied("No")

        return {"cohort": cohort, "user": user}

    def perform_create(self, serializer):
        serializer.save()

class EnrollmentRecordListView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.EnrollmentRecordSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        managed_partners = user.partners.all()
        managed_records = EnrollmentRecord.objects.active().filter(
            offering__partner__in=managed_partners.values_list("id", flat=True)
        )
        return managed_records.select_related("user", "offering__partner")


def continue_learning(request, offering_id):
    offering = get_object_or_404(CohortOffering, id=offering_id)
    return redirect(compat.make_course_url(offering.offering.course_key))


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def enroll_member(request, offering_id):
    user = request.user
    offering = get_object_or_404(CohortOffering, id=offering_id)
    user_has_access = user.memberships.filter(cohort=offering.cohort).exists()
    if not user_has_access:
        raise PermissionDenied("Permission denied.")
    enrollment_data = compat.enroll_student(offering.offering.course_key, user.email)
    return Response(enrollment_data)
