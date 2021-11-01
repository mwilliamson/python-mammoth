.PHONY: test

test:
	_virtualenv/bin/pyflakes mammoth tests
	sh -c '. _virtualenv/bin/activate; nosetests tests'

.PHONY: test-all

test-all:
	tox

.PHONY: upload

upload: setup assert-converted-readme build-dist
	_virtualenv/bin/twine upload dist/*
	make clean

.PHONY: build-dist

build-dist:
	rm -rf dist
	_virtualenv/bin/pyproject-build

README: README.md
	pandoc --from=markdown --to=rst README.md > README || cp README.md README

.PHONY: assert-converted-readme

assert-converted-readme:
	test "`cat README`" != "`cat README.md`"

.PHONY: clean

clean:
	rm -f README
	rm -f MANIFEST
	rm -rf dist

.PHONY: bootstrap

bootstrap: _virtualenv setup
	_virtualenv/bin/pip install -e .
ifneq ($(wildcard test-requirements.txt),)
	_virtualenv/bin/pip install -r test-requirements.txt
endif
	make clean

.PHONY: setup

setup: README

_virtualenv:
	python3 -m venv _virtualenv
	_virtualenv/bin/pip install --upgrade pip
	_virtualenv/bin/pip install --upgrade setuptools
	_virtualenv/bin/pip install --upgrade wheel
	_virtualenv/bin/pip install --upgrade build twine
