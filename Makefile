.PHONY: clean publish test docs

PYTHON ?= python
PYTEST ?= pytest
PY_TEST ?= py.test

dist :
	$(PYTHON) setup.py sdist --formats=gztar,zip
	$(PYTHON) setup.py bdist_wheel --python-tag=py3

deb_dist:
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

publish :
	twine upload dist/*.tar.gz dist/*.whl

test:
	$(PYTEST) -v

coverage:
	$(PY_TEST) --cov=toot --cov-report html tests/

clean :
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist MANIFEST htmlcov deb_dist toot*.tar.gz

changelog:
	./scripts/generate_changelog > CHANGELOG.md
