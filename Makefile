.DEFAULT_GOAL := help

.PHONY: help		# shows available commands
help:
	@echo "\nAvailable commands:\n\n $(shell sed -n 's/^.PHONY:\(.*\)/ *\1\\n/p' Makefile)"

.PHONY: test		# runs tests
test:
	coverage run setup.py test

.PHONY: test_all		# runs tests using detox, combines coverage and reports it
test_all:
	detox
	make coverage

.PHONY: coverage		# combines coverage and reports it
coverage:
	coverage combine || true
	coverage report

.PHONY: lint                # runs flake8, black and isort checks
lint:
	@flake8 bananas && echo "flake8 OK"
	black --check bananas
	isort --check -rc bananas

.PHONY: type-check
type-check:
	mypy

.PHONY: install
install:
	python setup.py install

.PHONY: develop
develop:
	python setup.py develop

CONTAINER ?= django2
.PHONY: attach
attach:
	docker attach --detach-keys="ctrl-d" `docker-compose ps -q $(CONTAINER)`

.PHONY: example		# starts example app using docker
example:
	@docker-compose up -d --build --force-recreate
	@rm -rf example/db.sqlite3
	@docker-compose run --rm django1 migrate --no-input
	@docker-compose run --rm django1 syncpermissions
	@docker-compose run --rm django1 createsuperuser \
	 	--username admin \
		--email admin@example.com
	@docker-compose ps

.PHONY: clean
clean:
	@rm -rf dist/ *.egg *.egg-info .coverage .coverage.* example/db.sqlite3

.PHONY: build
build: clean
	python3 -m pip install --upgrade wheel twine setuptools
	python3 setup.py sdist bdist_wheel

.PHONY: publish
publish: build
	python3 -m twine upload dist/*

.PHONY: test-publish
test-publish: build
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: all			# runs clean, test_all, lint, type-check
all: clean test_all lint type-check

.PHONY: isort
isort:
	isort -rc bananas

.PHONY: black
black:
	black bananas

.PHONY: format
format: black isort
