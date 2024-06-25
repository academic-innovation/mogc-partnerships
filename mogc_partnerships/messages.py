from edx_ace import ace
from edx_ace.message import MessageType
from edx_ace.recipient import Recipient

class CohortMembershipInviteMessage(MessageType):
    NAME = "cohort_invite"


cohort_membership_invite_message_type = CohortMembershipInviteMessage(
    context={
        "body": "Welcome to the cohort!"
    }
)


def send_message(msg):
    """
        Triggers a prepared custom message via edX ACE.
    """
    ace.send(msg)


def send_cohort_membership_invite(user):
    """
        Triggers an invitation email to new users in a cohort.
    """
    user_context = {"user": "Some additional content based on this user"}
    recipient = Recipient(lms_user_id=user.id, email_address=user.email)
    msg = cohort_membership_invite_message_type.personalize(
        recipient=recipient,
        language="en",
        user_context=user_context
    )

    send_message(msg)


def send_cohort_membership_invites(cohort_memberships):
    for member in cohort_memberships:
        send_cohort_membership_invite(member)
