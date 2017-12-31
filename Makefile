default : clean dist

dist :
	@echo "\nMaking source"
	@echo "-------------"
	@python setup.py sdist

	@echo "\nMaking wheel"
	@echo "-------------"
	@python setup.py bdist_wheel --universal

	@echo "\nDone."

clean :
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist MANIFEST htmlcov deb_dist toot*.tar.gz

publish :
	twine upload dist/*

coverage:
	py.test --cov=toot --cov-report html tests/

deb:
	@python setup.py --command-packages=stdeb.command bdist_deb
