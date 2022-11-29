.PHONY: clean publish test docs

dist :
	python setup.py sdist --formats=gztar,zip
	python setup.py bdist_wheel --python-tag=py3

publish :
	twine upload dist/*.tar.gz dist/*.whl

test:
	pytest -v

coverage:
	coverage erase
	coverage run
	coverage report

clean :
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist MANIFEST htmlcov toot*.tar.gz

changelog:
	./scripts/generate_changelog > CHANGELOG.md
