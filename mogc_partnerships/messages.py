from enum import Enum
from edx_ace import ace
from edx_ace.message import Message
from edx_ace.recipient import Recipient


class InvalidNotificationType(Exception):
    pass


class NotificationType(Enum):
    COHORT_INVITE = 1


notification_type_map = {NotificationType.COHORT_INVITE: "cohort_invite"}


def send_message(notification_type, member, context=None):
    """
    Triggers a prepared custom message via edX ACE.
    """
    try:
        notification_name = notification_type_map[notification_type]
    except KeyError:
        raise InvalidNotificationType(
            "{} is not a valid notification type".format(notification_type)
        )

    msg = Message(
        name=notification_name,
        app_label="partner_emails",
        recipient=Recipient(lms_user_id=member.id, email_address=member.email),
        language="en",
        context=context or {},
    )
    ace.send(msg)


def send_cohort_membership_invite(member):
    """
    Triggers an invitation email to new users in a cohort.
    """
    cohort = member.cohort
    user = member.user
    context = {
        "user": {"first_name": user.first_name if user else ""},
        "cohort": {
            "name": cohort.name,
            "uuid": cohort.uuid,
        },
        "partner": {
            "name": cohort.partner.name,
            "slug": cohort.partner.slug,
            "org": cohort.partner.org,
        },
    }
    send_message(NotificationType.COHORT_INVITE, member=member, context=context)
