UV := UV_CACHE_DIR=.uv-cache ./.tools/uv/uv

.PHONY: setup fetch-data validate-data build-data coverage test lint typecheck
setup:
	$(UV) sync

fetch-data:
	$(UV) run wcstrategy data fetch --season 2022

validate-data:
	$(UV) run wcstrategy data validate --season 2022

build-data:
	$(UV) run wcstrategy data build-canonical --season 2022

coverage:
	$(UV) run wcstrategy data coverage --season 2022

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

typecheck:
	$(UV) run mypy src

