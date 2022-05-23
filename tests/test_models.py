import pytest

from mogc_partnerships import factories


@pytest.mark.django_db
class TestPartner:
    def test_str(self):
        partner = factories.PartnerFactory(name="Gizmonic Institute")
        assert str(partner) == "Gizmonic Institute"
