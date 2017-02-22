.PHONY: test
test:
	python setup.py test

.PHONY: lint
lint:
	flake8 bananas

.PHONY: install
install:
	python setup.py install

.PHONY: develop
develop:
	python setup.py develop

.PHONY: coverage
coverage:
	coverage run setup.py test
	coverage report

.PHONY: clean
clean:
	rm -rf dist/ *.egg *.egg-info .coverage
