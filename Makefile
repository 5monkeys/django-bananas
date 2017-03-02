.DEFAULT_GOAL := help

.PHONY: help  # shows available commands
help:
	@echo "\nAvailable commands:\n\n $(shell sed -n 's/^.PHONY:\(.*\)/ *\1\\n/p' Makefile)"

.PHONY: test  # runs tests using detox, combines coverage and reports it
test:
	detox
	coverage combine
	coverage report

.PHONY: lint  # runs flake8
lint:
	flake8 bananas

.PHONY: install
install:
	python setup.py install

.PHONY: develop
develop:
	python setup.py develop

.PHONY: clean
clean:
	rm -rf dist/ *.egg *.egg-info .coverage .coverage.*

.PHONY: all  # runs clean, test, lint
all: clean test lint
