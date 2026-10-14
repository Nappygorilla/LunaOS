.PHONY: check test build
check:
	bash scripts/check-project.sh

test:
	python scripts/test-profiles.py
	python scripts/test-control-center.py

build:
	./build-lunaos.sh
