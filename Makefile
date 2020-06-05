INOTIFY_CALL ?= inotifywait -e modify -r ./powerfulseal ./tests
TOX_CALL ?= tox -r
METRICS_SERVER_URL ?= http://metrics-server.kube-system.svc.kubernetes.cluster/
CLOUD_OPTION ?= --openstack
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

# EXAMPLES OF RUNNING THE SEAL
autonomous:
	seal \
		-vv \
		autonomous \
			${CLOUD_OPTION} \
			--policy-file ./examples/policy_kill_random_default.yml \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 9999 \
			--ssh-allow-missing-host-keys \
			--host 0.0.0.0 \
			--port 30100

autonomous-headless:
	seal \
		-vv \
		autonomous \
			--headless \
			${CLOUD_OPTION} \
			--policy-file ./examples/policy_kill_random_default.yml \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 9999 \
			--ssh-allow-missing-host-keys

interactive:
	seal \
		-vv \
		interactive \
			${CLOUD_OPTION} \
			--inventory-kubernetes \
			--ssh-allow-missing-host-keys

validate:
	seal \
		-vv \
		validate \
			--policy-file ./examples/policy_kill_random_default.yml

label:
	seal \
		-vv \
		label \
			${CLOUD_OPTION} \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 9999 \
			--min-seconds-between-runs 3 \
			--max-seconds-between-runs 10 \
			--ssh-allow-missing-host-keys



# THE EXAMPLES BELOW SHOULD WORK FOR MINIKUBE
minikube-autonomous:
	seal \
		-vv \
		autonomous \
			--no-cloud \
			--policy-file ./examples/policy_kill_random_default.yml \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 9999 \
			--ssh-allow-missing-host-keys \
			--remote-user docker \
			--ssh-path-to-private-key `minikube ssh-key` \
			--override-ssh-host `minikube ip` \
			--host 0.0.0.0 \
			--port 30100

minikube-label:
	seal \
		-vv \
		label \
			--no-cloud \
			--min-seconds-between-runs 3 \
			--max-seconds-between-runs 10 \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 9999 \
			--ssh-allow-missing-host-keys \
			--remote-user docker \
			--ssh-path-to-private-key `minikube ssh-key` \
			--override-ssh-host `minikube ip`

minikube-interactive:
	seal \
		-vv \
		interactive \
			--no-cloud \
			--inventory-kubernetes \
			--ssh-allow-missing-host-keys \
			--remote-user docker \
			--ssh-path-to-private-key `minikube ssh-key` \
			--override-ssh-host `minikube ip`

docs: $(SCHEMA_FILE)
	# https://coveooss.github.io/json-schema-for-humans/
	pip install PyYAML json-schema-for-humans
	cat $(SCHEMA_FILE) | python -c "import sys; import yaml; import json; print(json.dumps(yaml.safe_load(sys.stdin.read()), indent=4, sort_keys=True))" > tmp.json
	mkdir -p docs/schema
	generate-schema-doc --no-minify --expand-buttons tmp.json docs/schema/index.html
	rm tmp.json

.PHONY: test watch upload clean build tag push version autonomous autonomous-headless interactive validate label minikube-autonomous minikube-label minikube-interactive

