from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from edx_django_utils.plugins.constants import PluginSettings, PluginSignals, PluginURLs

from .patches import patch_skip_activation_email

PROJECT_TYPE_LMS = "lms.djangoapp"
PROJECT_TYPE_CMS = "cms.djangoapp"


class PartnershipsAppConfig(AppConfig):
    name = "mogc_partnerships"
    verbose_name = _("Global Classroom partnerships")
    plugin_app = {
        PluginURLs.CONFIG: {
            PROJECT_TYPE_LMS: {
                PluginURLs.NAMESPACE: "mogc_partnerships",
                PluginURLs.REGEX: "^api/",
                PluginURLs.RELATIVE_PATH: "urls",
            }
        },
        PluginSettings.CONFIG: {
            PROJECT_TYPE_LMS: {
                "common": {PluginSettings.RELATIVE_PATH: "settings.common"}
            }
        },
        PluginSignals.CONFIG: {
            PROJECT_TYPE_CMS: {
                PluginSignals.RELATIVE_PATH: "receivers",
                PluginSignals.RECEIVERS: [
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: "create_offering_on_publish",
                        PluginSignals.SIGNAL_PATH: (
                            "xmodule.modulestore.django.COURSE_PUBLISHED"
                        ),
                    },
                ],
            },
            PROJECT_TYPE_LMS: {
                PluginSignals.RELATIVE_PATH: "receivers",
                PluginSignals.RECEIVERS: [
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: "link_user_to_invite",
                        PluginSignals.SIGNAL_PATH: (
                            "openedx_events.learning.signals."
                            "STUDENT_REGISTRATION_COMPLETED"
                        ),
                    },
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: "update_enrollment_records",
                        PluginSignals.SIGNAL_PATH: (
                            "openedx_events.learning.signals."
                            "COURSE_ENROLLMENT_CREATED"
                        ),
                    },
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: "update_enrollment_records",
                        PluginSignals.SIGNAL_PATH: (
                            "openedx_events.learning.signals."
                            "COURSE_UNENROLLMENT_COMPLETED"
                        ),
                    },
                ],
            },
        },
    }

    def ready(self):
        patch_skip_activation_email()
