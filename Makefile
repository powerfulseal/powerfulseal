INOTIFY_CALL ?= inotifywait -e modify -r ./powerfulseal ./tests
PYTEST_CALL ?= pytest --cov powerfulseal/ --cov-report term-missing -vv

test:
	$(PYTEST_CALL)

watch:
	$(PYTEST_CALL) && while $(INOTIFY_CALL); do $(PYTEST_CALL); done

upload:
	rm -rfv dist
	rm -rfv powerfulseal.egg-info
	python setup.py sdist
	twine upload dist/*

.PHONY: test watch
