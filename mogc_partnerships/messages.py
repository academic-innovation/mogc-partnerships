from edx_ace import ace
from edx_ace.message import MessageType
from edx_ace.recipient import Recipient

class CohortMembershipInviteMessage(MessageType):
    NAME = "cohort_invite"


cohort_membership_invite_message_type = CohortMembershipInviteMessage()


def send_message(msg):
    """
        Triggers a prepared custom message via edX ACE.
    """
    ace.send(msg)


def send_cohort_membership_invite(member):
    """
        Triggers an invitation email to new users in a cohort.
    """
    cohort = member.cohort
    user = member.user
    context = {
        "user": {
            user.name or ""
        },
        "cohort": {
            "name": cohort.name,
            "uuid": cohort.uuid,
        },
        "partner": {
            "name": cohort.partner.name,
            "slug": cohort.partner.slug,
            "org": cohort.partner.org
        }
    }
    recipient = Recipient(lms_user_id=member.id, email_address=member.email)
    msg = cohort_membership_invite_message_type.personalize(
        recipient=recipient,
        language="en",
        context=context
    )

    send_message(msg)


def send_cohort_membership_invites(cohort_memberships):
    for member in cohort_memberships:
        send_cohort_membership_invite(member)
