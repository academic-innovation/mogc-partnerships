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
    session.install("django~=3.2.0")
    session.install("-r", "requirements.txt")
    session.run("python", "manage.py", "makemigrations", "--check")


@nox.session
def test(session):
    """Runs tests with pytest."""
    session.install("django~=3.2.0")
    session.install("-r", "requirements.txt")
    session.run("pytest")
