import pytest

from mogc_partnerships import factories, messages


@pytest.mark.django_db
class TestMessages:
    """Tests for messages - email notifications sent via edx-ace"""

    def _setup(self, with_user=False):
        self.manager = factories.PartnerManagementMembershipFactory()
        self.cohort = factories.PartnerCohortFactory(partner=self.manager.partner)
        self.member = factories.CohortMembershipFactory(cohort=self.cohort)
        if with_user:
            self.user = factories.UserFactory()
            self.member.user = self.user

    def test_send_message_with_valid_type(self, mocker):
        """Messages with a valid NotificationType should send successfully"""
        self._setup(with_user=True)

        mocker.patch("edx_ace.ace.send")
        messages.send_message(
            messages.cohort_membership_invite, self.member, context={"foo": "bar"}
        )

    def test_send_cohort_membership_invite_existing_user(self, mocker):
        """Cohort Invite email should send to existing users and include user details in context"""
        self._setup(with_user=True)

        mocker.patch("edx_ace.ace.send")
        messages.send_cohort_membership_invite(self.member)

    def test_send_cohort_membership_invite_new_user(self, mocker):
        """Cohort Invite email should send to new/non-users and exclude user details"""
        self._setup()

        mocker.patch("edx_ace.ace.send")
        messages.send_cohort_membership_invite(self.member)
