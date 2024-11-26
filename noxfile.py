import nox


@nox.session
def lint(session):
    """Checks for linting errors with flake8."""
    session.install("-r", "requirements.txt")
    session.run("flake8")


@nox.session
def sort(session):
    """Checks that imports are correctly sorted using isort."""
    session.install("-r", "requirements.txt")
    session.run("isort", ".", "--check")


@nox.session
def format(session):
    """Checks that code is correctly formatted using black."""
    session.install("-r", "requirements.txt")
    session.run("black", ".", "--check")


@nox.session
def migrations(session):
    """Checks that all expected migrations are present."""
    session.install("django~=4.2.0")
    session.install("-r", "requirements.txt")
    session.run("python", "manage.py", "makemigrations", "--check")


@nox.session
@nox.parametrize(
    "python,django",
    [
        (python, django)
        for python in ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")
        for django in ("3.2.0", "4.2.0", "5.0.0", "5.1.0")
        if (python, django)
        not in [
            ("3.8", "5.0.0"),
            ("3.8", "5.1.0"),
            ("3.9", "5.0.0"),
            ("3.9", "5.1.0"),
            ("3.11", "3.2.0"),
            ("3.12", "3.2.0"),
            ("3.13", "3.2.0"),
        ]
    ],
)
def test(session, django):
    """Runs tests with pytest."""
    session.install(f"django~={django}")
    session.install("-r", "requirements.txt")
    session.run("pytest")
