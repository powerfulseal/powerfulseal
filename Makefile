INOTIFY_CALL ?= inotifywait -e modify -r ./powerfulseal ./tests
TOX_CALL ?= tox -r

test:
	$(TOX_CALL)

watch:
	$(TOX_CALL) && while $(INOTIFY_CALL); do $(TOX_CALL); done

upload:
	rm -rfv dist
	rm -rfv powerfulseal.egg-info
	python setup.py sdist
	twine upload dist/*

.PHONY: test watch
