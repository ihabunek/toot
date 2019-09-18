.PHONY: clean publish test

dist :
	python setup.py sdist --formats=gztar,zip
	python setup.py bdist_wheel --python-tag=py3

deb_dist:
	python setup.py --command-packages=stdeb.command bdist_deb

publish :
	twine upload dist/*.tar.gz dist/*.whl

test:
	pytest -v

coverage:
	py.test --cov=toot --cov-report html tests/

clean :
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist MANIFEST htmlcov deb_dist toot*.tar.gz

changelog:
	./scripts/generate_changelog > CHANGELOG.md
