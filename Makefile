.DEFAULT_GOAL := help

.PHONY: help		# shows available commands
help:
	@echo "\nAvailable commands:\n\n $(shell sed -n 's/^.PHONY:\(.*\)/ *\1\\n/p' Makefile)"

.PHONY: test		# runs tests
test:
	python -X dev -Wd -m coverage run runtests.py $(test)

.PHONY: test_all		# runs tests using detox, combines coverage and reports it
test_all:
	detox
	make coverage

.PHONY: test-types      # runs pytest-mypy-plugins to test exported types
test-types:
	pytest --mypy-ini-file=setup.cfg tests/*.yaml

.PHONY: coverage		# combines coverage and reports it
coverage:
	coverage combine || true
	coverage report

coverage-xml:
	coverage combine || true
	coverage xml -o coverage.xml

.PHONY: lint                # runs flake8, black and isort checks
lint:
	@flake8 bananas tests && echo "flake8 OK"
	black --check bananas tests
	isort --check bananas tests

.PHONY: type-check
type-check:
	mypy $(type-check)

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
	isort bananas tests

.PHONY: black
black:
	black bananas tests

.PHONY: autoflake
autoflake:
	autoflake \
		--recursive \
		--in-place \
		--remove-all-unused-imports \
		--ignore-init-module-imports \
		bananas tests

.PHONY: format
format: black isort autoflake
