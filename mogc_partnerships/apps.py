from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from edx_django_utils.plugins.constants import PluginSignals, PluginURLs

PROJECT_TYPE_LMS = "lms.djangoapp"


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
        PluginSignals.CONFIG: {
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
                ],
            }
        },
    }
