COURSE_ENROLLMENT_STARTED = "org.openedx.learning.course.enrollment.started.v1"


def plugin_settings(settings):
    settings.OPEN_EDX_FILTERS_CONFIG = {
        COURSE_ENROLLMENT_STARTED: {
            "fail_silently": False,
            "pipeline": ["mogc_partnerships.pipeline.MembershipRequiredEnrollment"],
        },
    }
