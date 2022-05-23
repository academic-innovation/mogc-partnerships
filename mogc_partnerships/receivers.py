from django.contrib.auth import get_user_model

from openedx_events.learning.data import CourseEnrollmentData, UserData

from .models import CatalogMembership, EnrollmentRecord, PartnerOffering


def link_user_to_invite(user: UserData, **kwargs):
    AuthUser = get_user_model()
    email = user.pii.email
    auth_user = AuthUser.objects.get(email=email)
    CatalogMembership.objects.filter(email=email, user=None).update(user=auth_user)


def update_enrollment_records(enrollment: CourseEnrollmentData, **kwargs):
    course_key = enrollment.course.course_key
    user_id = enrollment.user.id
    AuthUser = get_user_model()
    user = AuthUser.objects.get(id=user_id)
    offerings = PartnerOffering.objects.filter(course_key=course_key)
    for offering in offerings:
        EnrollmentRecord.objects.update_or_create(
            user=user,
            offering=offering,
            defaults={
                "mode": enrollment.mode,
                "is_active": enrollment.is_active,
                "creation_date": enrollment.creation_date,
            },
        )
