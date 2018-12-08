INOTIFY_CALL ?= inotifywait -e modify -r ./powerfulseal ./tests
NPM_CALL ?= cd powerfulseal/web/ui && npm install && npm run build
TOX_CALL ?= tox -r

test:
	$(TOX_CALL)

watch:
	$(TOX_CALL) && while $(INOTIFY_CALL); do $(TOX_CALL); done

web:
	$(NPM_CALL)

upload:
	rm -rfv dist
	rm -rfv powerfulseal.egg-info
	python setup.py sdist
	twine upload dist/*

run-openstack:
	seal \
		--verbose \
		autonomous \
			--kubeconfig ~/.kube/config \
			--openstack \
			--policy-file ./tests/policy/example_config.yml \
			--inventory-kubernetes \
			--prometheus-collector \
			--prometheus-host 0.0.0.0 \
			--prometheus-port 30101 \
			--ssh-allow-missing-host-keys \
			--host 0.0.0.0 \
			--port 30100

.PHONY: test watch web run-openstack
