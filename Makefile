.PHONY: clean publish test docs

dist:
	python -m build

publish :
	twine upload dist/*.tar.gz dist/*.whl

test:
	pytest -v
	flake8
	vermin toot

coverage:
	coverage erase
	coverage run
	coverage html --omit "toot/tui/*"
	coverage report

clean :
	find . -name "*pyc" | xargs rm -rf $1
	rm -rf build dist MANIFEST htmlcov bundle toot*.tar.gz toot*.pyz

changelog:
	./scripts/generate_changelog > CHANGELOG.md
	cp CHANGELOG.md docs/changelog.md

docs: changelog
	mdbook build

docs-serve:
	mdbook serve --port 8000

docs-deploy: docs
	rsync --archive --compress --delete --stats book/ bezdomni:web/toot

.PHONY: bundle
bundle:
	mkdir bundle
	cp toot/__main__.py bundle
	pip install . --target=bundle
	rm -rf bundle/*.dist-info
	find bundle/ -type d -name "__pycache__" -exec rm -rf {} +
	python -m zipapp \
		--python "/usr/bin/env python3" \
		--output toot-`git describe`.pyz bundle \
		--compress
	echo "Bundle created: toot-`git describe`.pyz"
