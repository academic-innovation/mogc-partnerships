def make_course_url(course_key):
    try:
        from openedx.features.course_experience.url_helpers import (  # type: ignore
            get_learning_mfe_home_url,
        )

        return get_learning_mfe_home_url(course_key)
    except ImportError:
        return "/"


def enroll_student(course_key, student_email):
    try:
        from lms.djangoapps.instructor import enrollment  # type: ignore

        previous_state, after_state, enrollment_obj = enrollment.enroll_email(
            course_key, student_email, auto_enroll=True
        )
        return {
            "course_id": str(course_key),
            "enrolled": after_state.enrollment,
            "course_home_url": make_course_url(course_key),
        }
    except ImportError:
        return {
            "course_id": str(course_key),
            "enrolled": False,
            "course_home_url": make_course_url(course_key),
        }
