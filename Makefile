test:
	python setup.py test

flake8:
	flake8 bananas

install:
	python setup.py install

develop:
	python setup.py develop

coverage:
	coverage run --source bananas setup.py test

clean:
	rm -rf dist/ *.egg *.egg-info .coverage
