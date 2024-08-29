SRC_DIRS = ./mogc_partnerships
BLACK_OPTS = --exclude templates ${SRC_DIRS}

format:
	black $(BLACK_OPTS)

lint:
	flake8

isort:
	isort --skip=templates ${SRC_DIRS}

test:
	pytest

quality:
	make format && make lint && make isort