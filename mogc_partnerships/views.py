from django.contrib.auth import get_user_model
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
    CatalogMembership,
    CatalogOffering,
    EnrollmentRecord,
    Partner,
    PartnerCatalog,
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


class CatalogListView(generics.ListCreateAPIView):
    """List and create catalogs."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PartnerCatalogSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        memberships = PartnerManagementMembership.objects.filter(user=user)
        return PartnerCatalog.objects.filter(
            partner__in=memberships.values_list("partner_id", flat=True)
        )

    def perform_create(self, serializer):
        partner = serializer.validated_data["partner"]
        if self.request.user not in partner.managers.all():
            self.permission_denied(
                self.request, f"Cannot create catalog for {partner.slug}"
            )
        return super().perform_create(serializer)


class CatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Allows managers to update and delete catalogs for their partners."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.PartnerCatalogUpdateSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        user = self.request.user
        return PartnerCatalog.objects.filter(
            partner__in=user.partners.values_list("id", flat=True)
        )


class CatalogOfferingListView(generics.ListAPIView):
    """Lists catalog offerings."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CatalogOfferingSerializer
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
        managed_offerings = CatalogOffering.objects.filter(
            catalog__partner_id__in=managed_partners.values_list("id", flat=True)
        )
        memberships = user.memberships.all()
        member_offerings = CatalogOffering.objects.filter(
            catalog__in=memberships.values_list("catalog_id", flat=True)
        )
        accessible_offerings = managed_offerings | member_offerings
        return accessible_offerings.select_related("offering")


class CatalogOfferingCreateView(generics.CreateAPIView):
    """Adds offerings to catalogs."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CatalogOfferingSerializer

    def perform_create(self, serializer):
        user = self.request.user
        managed_catalogs = PartnerCatalog.objects.filter(
            partner__in=user.partners.values_list("id", flat=True)
        )
        catalog_uuid = self.kwargs.get("catalog_uuid")
        try:
            catalog = managed_catalogs.get(uuid=catalog_uuid)
        except PartnerCatalog.DoesNotExist:
            raise PermissionDenied("No")
        offering = serializer.validated_data["offering"]
        if offering not in catalog.partner.offerings.all():
            raise PermissionDenied("No!")
        serializer.save(catalog=catalog)


class CatalogMembershipListView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CatalogMembershipSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        managed_memberships = CatalogMembership.objects.filter(
            catalog__partner__in=user.partners.values_list("id", flat=True)
        )
        return managed_memberships.select_related("catalog__partner", "user")


class CatalogMembershipCreateView(generics.CreateAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.CatalogMembershipSerializer

    def perform_create(self, serializer):
        user = self.request.user
        managed_partners = Partner.objects.active().for_user(user)
        managed_catalogs = PartnerCatalog.objects.filter(
            partner__in=managed_partners.values_list("id", flat=True)
        )
        catalog_uuid = self.kwargs.get("catalog_uuid")
        try:
            catalog = managed_catalogs.get(uuid=catalog_uuid)
        except PartnerCatalog.DoesNotExist:
            raise PermissionDenied("No")
        email = serializer.validated_data.get("email")
        User = get_user_model()
        try:
            membership_account = User.objects.get(email=email)
        except User.DoesNotExist:
            membership_account = None
        serializer.save(catalog=catalog, user=membership_account)


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
        return managed_records.select_related("offering__partner")


def continue_learning(request, offering_id):
    offering = get_object_or_404(CatalogOffering, id=offering_id)
    return redirect(compat.make_course_url(offering.offering.course_key))


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def enroll_member(request, offering_id):
    user = request.user
    offering = get_object_or_404(CatalogOffering, id=offering_id)
    user_has_access = user.memberships.filter(catalog=offering.catalog).exists()
    if not user_has_access:
        raise PermissionDenied("Permission denied.")
    enrollment_data = compat.enroll_student(offering.offering.course_key, user.email)
    return Response(enrollment_data)
