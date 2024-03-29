# Generated by Django 3.2.17 on 2023-09-06 17:30

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import opaque_keys.edx.django.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Partner",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
                (
                    "org",
                    models.CharField(
                        help_text="The Open edX orginization code associated with this partner.",
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PartnerOffering",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "course_key",
                    opaque_keys.edx.django.models.CourseKeyField(max_length=255),
                ),
                ("title", models.CharField(max_length=255)),
                ("short_description", models.CharField(max_length=500)),
                ("description", models.TextField()),
                (
                    "partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offerings",
                        to="mogc_partnerships.partner",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PartnerManagementMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="management_memberships",
                        to="mogc_partnerships.partner",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="management_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PartnerCohort",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                ("uuid", models.UUIDField(default=uuid.uuid4)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "partner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cohorts",
                        to="mogc_partnerships.partner",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="partner",
            name="managers",
            field=models.ManyToManyField(
                related_name="partners",
                through="mogc_partnerships.PartnerManagementMembership",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="EnrollmentRecord",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("mode", models.CharField(max_length=64)),
                ("grade", models.PositiveSmallIntegerField(default=0)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                ("is_complete", models.BooleanField(default=False)),
                ("is_successful", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "creation_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "offering",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollment_records",
                        to="mogc_partnerships.partneroffering",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollment_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CohortOffering",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "cohort",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offerings",
                        to="mogc_partnerships.partnercohort",
                    ),
                ),
                (
                    "offering",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mogc_partnerships.partneroffering",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CohortMembership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(max_length=254)),
                (
                    "cohort",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="mogc_partnerships.partnercohort",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="partneroffering",
            constraint=models.UniqueConstraint(
                fields=("partner", "course_key"), name="unique_course_key_per_partner"
            ),
        ),
        migrations.AddConstraint(
            model_name="partnermanagementmembership",
            constraint=models.UniqueConstraint(
                fields=("partner", "user"), name="unique_user_per_partner"
            ),
        ),
        migrations.AddConstraint(
            model_name="enrollmentrecord",
            constraint=models.UniqueConstraint(
                fields=("user", "offering"), name="unique_user_per_offering"
            ),
        ),
        migrations.AddConstraint(
            model_name="cohortoffering",
            constraint=models.UniqueConstraint(
                fields=("cohort", "offering"), name="unique_offering_per_cohort"
            ),
        ),
        migrations.AddConstraint(
            model_name="cohortmembership",
            constraint=models.UniqueConstraint(
                fields=("cohort", "email"), name="unique_email_per_cohort"
            ),
        ),
        migrations.AddConstraint(
            model_name="cohortmembership",
            constraint=models.UniqueConstraint(
                fields=("cohort", "user"), name="unique_user_per_cohort"
            ),
        ),
    ]
