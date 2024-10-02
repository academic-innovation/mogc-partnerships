from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect

from rest_framework import generics, status
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

from . import compat, tasks
from .lib import get_cohort
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
from .permissions import ManagerCreatePermission, ManagerEditPermission


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
    permission_classes = [IsAuthenticated, ManagerCreatePermission]
    serializer_class = serializers.PartnerCohortSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        memberships = PartnerManagementMembership.objects.filter(user=user)
        return PartnerCohort.objects.filter(
            partner__in=memberships.values_list("partner_id", flat=True)
        )

    def perform_create(self, serializer):
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
        context["enrollments"] = self.request.user.enrollment_records.filter(is_active=True).values_list(
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
    permission_classes = [IsAuthenticated, ManagerEditPermission]
    serializer_class = serializers.CohortOfferingSerializer

    def perform_create(self, serializer):
        cohort = get_cohort(self.request.user, self.kwargs.get("cohort_uuid"))
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
    permission_classes = [IsAuthenticated, ManagerEditPermission]
    serializer_class = serializers.CohortMembershipSerializer

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super(CohortMembershipCreateView, self).get_serializer(*args, **kwargs)

    def create_collection(self, validated_data, cohort):
        member_emails = [od["email"] for od in validated_data]

        User = get_user_model()
        membership_accounts = User.objects.filter(
            email__in=[email for email in member_emails]
        )
        account_email_map = {user.email: user for user in membership_accounts}

        cohort_memberships = [
            CohortMembership(
                user=account_email_map.get(member_email),
                cohort=cohort,
                email=member_email,
            )
            for member_email in member_emails
        ]

        objects = CohortMembership.objects.bulk_create(
            cohort_memberships, ignore_conflicts=True
        )
        # bulk_create doesn't return autoincremented IDs with MySQL DBs
        # so we have to query results separately
        cohort_memberships = CohortMembership.objects.filter(
            email__in=[cm.email for cm in objects], cohort=cohort
        )

        tasks.trigger_send_cohort_membership_invites(cohort_memberships)

        return cohort_memberships

    def create_instance(self, validated_data, cohort):
        validated_data["cohort"] = cohort

        User = get_user_model()
        try:
            validated_data["user"] = User.objects.get(email=validated_data.get("email"))
        except User.DoesNotExist:
            validated_data["user"] = None

        cohort_membership = CohortMembership.objects.create(**validated_data)

        tasks.trigger_send_cohort_membership_invite(cohort_membership)

        return cohort_membership

    def create(self, request, *args, **kwargs):
        cohort = get_cohort(request.user, kwargs.get("cohort_uuid"))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        if isinstance(validated_data, list):
            memberships = self.create_collection(validated_data, cohort)
            return Response(
                self.serializer_class(memberships, many=True).data,
                status=status.HTTP_201_CREATED,
            )

        membership = self.create_instance(validated_data, cohort)
        return Response(
            self.serializer_class(membership).data, status=status.HTTP_201_CREATED
        )


class CohortMembershipUpdateView(generics.UpdateAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, ManagerEditPermission]
    serializer_class = serializers.CohortMembershipSerializer

    def get_queryset(self):
        return CohortMembership.objects.filter(
            pk=self.kwargs.get("pk"), cohort__uuid=self.kwargs.get("cohort_uuid")
        )

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset)

    def unenroll(self, cohort_member):
        """
        The same course can be offered via multiple cohorts within the same partner.

        Check if a user is enrolled in an offering, and unenroll iff the enrollment
        is not for an offering available in another cohort the user is also in.
        """
        user_enrollment_records = EnrollmentRecord.objects.select_related(
            "offering__partner"
        ).filter(user=cohort_member.user, is_active=True)
        if not user_enrollment_records:
            return

        user_cohort_ids = (
            CohortMembership.objects.filter(user=cohort_member.user)
            .filter(cohort__partner=cohort_member.cohort.partner)
            .values_list("cohort", flat=True)
        )

        # ID list of partner offerings in cohort member's cohort
        cohort_offering_ids = CohortOffering.objects.filter(
            cohort=cohort_member.cohort
        ).values_list("offering", flat=True)

        # ID list of partner offerings in other cohorts user is in
        partner_offering_ids = (
            CohortOffering.objects.select_related("offerings")
            .exclude(cohort=cohort_member.cohort)
            .filter(
                offering__partner=cohort_member.cohort.partner,
                cohort__in=user_cohort_ids,
            )
            .values_list("offering__pk", flat=True)
        )

        # Filter down to enrollments eligible for unenrollment
        eligible_enrollment_records = user_enrollment_records.exclude(
            Q(offering__id__in=partner_offering_ids) & Q(is_active=True),
            Q(offering__id__in=cohort_offering_ids),
        )
        if not eligible_enrollment_records:
            return

        eligible_enrollment_records.update(is_active=False)

        unenrollment_results = []
        for er in eligible_enrollment_records:
            result = compat.update_student_enrollment(
                er.offering.course_key,
                cohort_member.email,
                action=compat.UNENROLL_ACTION,
            )
            unenrollment_results.append(result)

    def perform_update(self, serializer):
        cohort_member = self.get_object()
        user = cohort_member.user
        if user:
            self.unenroll(cohort_member)

        return super().perform_update(serializer)


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
    enrollment_data = compat.update_student_enrollment(
        offering.offering.course_key, user.email, action=compat.ENROLL_ACTION
    )
    return Response(enrollment_data)
