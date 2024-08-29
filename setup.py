from setuptools import find_packages, setup

setup(
    name="mogc-partnerships",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "django>=3.2,<4.0",
        "edx-django-utils",
        "openedx-events>=0.8.1",
        "openedx-filters>=0.7.0",
        "edx-opaque-keys",
        "edx-ace",
    ],
    entry_points={
        "lms.djangoapp": [
            "mogc_partnerships = mogc_partnerships.apps:PartnershipsAppConfig",
        ],
        "cms.djangoapp": [
            "mogc_partnerships = mogc_partnerships.apps:PartnershipsAppConfig",
        ],
    },
)
