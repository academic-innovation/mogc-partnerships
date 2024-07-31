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
        Triggers a prepared custom message via edX ACE.
    """
    success = True
    try:
        recipient = Recipient(lms_user_id=member.id, email_address=member.email)
        msg = notification_type.personalize(
            recipient=recipient,
            language="en",
            user_context=context
        )
        ace.send(msg)
    except:
        success = False
        logger.error("Error sending {} notification to member {} - {}".format(notification_type, member.id, member.email))

    return success

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
        "base_url": "",
    }

    send_message(cohort_membership_invite, member, context)
