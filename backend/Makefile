.PHONY: fmt lint type test check

fmt:
	black app tests
	ruff check --fix app tests

lint:
	ruff check app tests

type:
	mypy app

test:
	pytest -v

# Tout vérifier d'un coup
check: fmt lint type test
