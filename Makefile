unittests: 
	venv/bin/python3 -m unittest tests/test_*.py

.PHONY: integrationtests
integrationtests: 
	venv/bin/python3 -m unittest tests/itest_*.py

localintegrationtests: container integrationtests clean


venv-test: venv
	if [ -f requirements-test.txt ]; then venv/bin/pip3 install -r requirements-test.txt; fi

container: clean
	podman run -d --rm --name iskurmountebank -p 2525:2525 -p 8080:8080 registry.gitlab.com/soerenschneider/mountebank-docker
	podman run -d --rm --name iskurpostgres -e POSTGRES_USER=iskur -e POSTGRES_PASSWORD=iskur -e POSTGRES_DB=iskur -p 127.0.0.1:5432:5432 postgres:12
	sleep 2
	curl -X POST --data @mountebank/darksky.json http://localhost:2525/imposters

clean:
	podman rm -f iskurmountebank || true
	podman rm -f iskurpostgres || true

.PHONY: venv
venv:
	if [ ! -d "venv" ]; then python3 -m venv venv; fi
	venv/bin/pip3 install -r requirements.txt
