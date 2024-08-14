import logging

logger = logging.getLogger(__name__)

ENROLL_ACTION = "enroll"
UNENROLL_ACTION = "unenroll"


class InvalidEnrollmentAction(Exception):
    pass


def make_course_url(course_key):
    try:
        from openedx.features.course_experience.url_helpers import (  # type: ignore
            get_learning_mfe_home_url,
        )

        return get_learning_mfe_home_url(course_key)
    except ImportError:
        return "/"


def update_student_enrollment(course_key, student_email, action):
    result = {
        "course_id": str(course_key),
        "course_home_url": make_course_url(course_key),
    }

    try:
        from lms.djangoapps.instructor import enrollment  # type: ignore

        if action == ENROLL_ACTION:
            previous_state, after_state, enrollment_obj = enrollment.enroll_email(
                course_key, student_email, auto_enroll=True
            )
        elif action == UNENROLL_ACTION:
            previous_state, after_state, enrollment_obj = enrollment.unenroll_email(
                course_key, student_email
            )
        else:
            raise InvalidEnrollmentAction(f"{action} is not a valid enrollment option")

        result.update({"enrolled": after_state.enrollment})
    except (ImportError, InvalidEnrollmentAction) as e:
        logger.error(e)
        result.update({"enrolled": False})

    return result


def get_course_overview_or_none(course_id):
    try:
        from openedx.core.djangoapps.content.course_overviews import api  # type: ignore

        return api.get_course_overview_or_none(course_id)
    except ImportError:
        return None
