INOTIFY_CALL ?= inotifywait -e modify -r ./powerfulseal ./tests
TOX_CALL ?= tox -r
SCHEMA_FILE=powerfulseal/policy/ps-schema.yaml

name ?= powerfulseal
version ?= `python setup.py --version`
tag = $(name):$(version)
namespace ?= "bloomberg/"

test:
	$(TOX_CALL)

watch:
	$(TOX_CALL) && while $(INOTIFY_CALL); do $(TOX_CALL); done

upload:
	rm -rfv dist
	rm -rfv powerfulseal.egg-info
	python setup.py sdist
	twine upload dist/*

clean:
	find -name '*.pyc' -delete
	find -name '__pycache__' -delete

build:
	docker build -t $(tag) -f ./build/Dockerfile .

tag:
	docker tag $(tag) $(namespace)$(tag)

push:
	docker push $(namespace)$(tag)

version:
	@echo $(tag)

docs: $(SCHEMA_FILE)
	# https://coveooss.github.io/json-schema-for-humans/
	pip install PyYAML json-schema-for-humans
	cat $(SCHEMA_FILE) | python -c "import sys; import yaml; import json; print(json.dumps(yaml.safe_load(sys.stdin.read()), indent=4, sort_keys=True))" > tmp.json
	mkdir -p docs/schema
	generate-schema-doc --no-minify --expand-buttons tmp.json docs/schema/index.html
	rm tmp.json

.PHONY: test watch upload clean build tag push version
