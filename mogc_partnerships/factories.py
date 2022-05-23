import factory
from factory.django import DjangoModelFactory

from . import models


class UserFactory(DjangoModelFactory):
    """Factory for auth User objects."""

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = "password"

    class Meta:
        model = "auth.User"
        django_get_or_create = ("username",)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class PartnerFactory(DjangoModelFactory):
    """Factory for Partner objects."""

    name = factory.Faker("company")
    slug = factory.Faker("slug")

    class Meta:
        model = models.Partner
        django_get_or_create = ("slug",)


class PartnerManagementMembershipFactory(DjangoModelFactory):
    """Factory for PartnerManagementMembership objects."""

    partner = factory.SubFactory(PartnerFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.PartnerManagementMembership


class PartnerOfferingFactory(DjangoModelFactory):
    """Factory for PartnerOffering objects."""

    partner = factory.SubFactory(PartnerFactory)
    course_key = factory.Sequence(
        lambda n: f"course-v1:MichiganOnline+MOGC10{n}+2022_T0"
    )
    title = factory.Faker("bs")
    short_description = factory.Faker("sentence")
    description = "<p>This is a course.</p>"

    class Meta:
        model = models.PartnerOffering


class PartnerCatalogFactory(DjangoModelFactory):
    """Factory for PartnerCatalog objects."""

    partner = factory.SubFactory(PartnerFactory)
    name = factory.Faker("word")

    class Meta:
        model = models.PartnerCatalog


class CatalogOfferingFactory(DjangoModelFactory):
    """Factory for CatalogOffering objects."""

    catalog = factory.SubFactory(PartnerCatalogFactory)
    offering = factory.SubFactory(
        PartnerOfferingFactory, partner=factory.SelfAttribute("..catalog.partner")
    )

    class Meta:
        model = models.CatalogOffering


class CatalogMembershipFactory(DjangoModelFactory):
    """Factory for CatalogMembership objects."""

    catalog = factory.SubFactory(PartnerCatalogFactory)
    email = factory.Faker("email")
    user = factory.SubFactory(UserFactory, email=factory.SelfAttribute("..email"))

    class Meta:
        model = models.CatalogMembership


class CatalogMembershipInviteFactory(CatalogMembershipFactory):
    user = None
