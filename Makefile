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
	rm -rf build dist *.egg-info MANIFEST

publish :
	twine upload dist/*
