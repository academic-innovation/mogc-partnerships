from rest_framework.exceptions import PermissionDenied

from .models import PartnerCohort


def get_cohort(user, cohort_uuid):
    try:
        managed_cohorts = PartnerCohort.objects.filter(
            partner__in=user.partners.values_list("id", flat=True)
        )
        cohort = managed_cohorts.get(uuid=cohort_uuid)
        return cohort
    except PartnerCohort.DoesNotExist:
        raise PermissionDenied("Partner cohort does not exist")
