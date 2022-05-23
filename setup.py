from setuptools import find_packages, setup

setup(
    name="mogc-partnerships",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "django>=3.2,<4.0",
        "edx-django-utils",
        "edx-opaque-keys",
    ],
    entry_points={
        "lms.djangoapp": [
            "mogc_partnerships = mogc_partnerships.apps:PartnershipsAppConfig",
        ],
    },
)
