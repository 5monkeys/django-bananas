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

.PHONY: lint		# runs flake8
lint:
	@flake8 bananas && echo "OK"

.PHONY: install
install:
	python setup.py install

.PHONY: develop
develop:
	python setup.py develop

.PHONY: example		# starts exmpale app using docker
example:
	@docker-compose up -d --build --force-recreate
	@rm -rf example/db.sqlite3
	@docker-compose run --rm django1 migrate --no-input
	@docker-compose run --rm django1 createsuperuser \
	 	--username admin \
		--email admin@example.com
	@docker-compose ps

.PHONY: clean
clean:
	@rm -rf dist/ *.egg *.egg-info .coverage .coverage.* example/db.sqlite3

.PHONY: all			# runs clean, test_all, lint
all: clean test_all lint
