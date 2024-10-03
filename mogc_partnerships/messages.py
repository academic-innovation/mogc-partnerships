import logging

from edx_ace import ace
from edx_ace.message import MessageType
from edx_ace.recipient import Recipient

logger = logging.getLogger(__name__)


class CohortMembershipInviteMessage(MessageType):
    APP_LABEL = "partner_emails"
    NAME = "cohort_invite"


cohort_membership_invite = CohortMembershipInviteMessage()


def send_message(notification_type, member, context):
    """
    Sends an email of notification_type to member with custom user context. User
    context data is combined with a default context object which can be set on the
    MessageType.
    """
    try:
        recipient = Recipient(lms_user_id=member.id, email_address=member.email)
        msg = notification_type.personalize(
            recipient=recipient, language="en", user_context=context
        )
        ace.send(msg)
    except Exception as e:
        logger.error(
            "Error sending {} notification to member {} - {}".format(
                notification_type, member.id, member.email
            )
        )
        raise (e)


def send_cohort_membership_invite(member):
    """
    Triggers an invitation email to new users in a cohort.
    """
    cohort = member.cohort
    partner = cohort.partner
    user = member.user

    base_url = "https://apps.learn.online.umich.edu/partners"
    next_url = "{}/{}/details".format(base_url, partner.slug)
    auth_path = "register" if not user else "login"
    login_url = "https://apps.learn.online.umich.edu/authn/{}/?next={}".format(
        auth_path, next_url
    )

    context = {
        "user": {"first_name": user.first_name if user else ""},
        "cohort": {
            "name": cohort.name,
            "uuid": cohort.uuid,
        },
        "partner": {
            "name": partner.name,
            "slug": partner.slug,
            "org": partner.org,
        },
        "login_url": login_url,
    }

    send_message(cohort_membership_invite, member, context)
