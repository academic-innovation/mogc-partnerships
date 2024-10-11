import logging

logger = logging.getLogger(__name__)


def patch_skip_activation_email():
    try:
        from openedx.core.djangoapps.user_authn.views import register
    except ImportError:
        return

    from .models import CohortMembership

    original_function = register._skip_activation_email

    def _skip_activation_email(
        user, running_pipeline, third_party_provider, *args, **kwargs
    ):
        logger.info("Using patched _skip_activation_email")

        if CohortMembership.objects.pending().filter(email=user.email).exists():
            return True

        return original_function(
            user, running_pipeline, third_party_provider, *args, **kwargs
        )

    register._skip_activation_email = _skip_activation_email
