UV := PYTHONPATH=src UV_CACHE_DIR=.uv-cache ./.tools/uv/uv

.PHONY: setup fetch-data validate-data build-data coverage test lint typecheck actions xg xt progression attacking-summary milestone-2 ppda pressure-events pressure-regains context360 pressure-summary milestone-3
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

actions:
	$(UV) run wcstrategy actions build-spadl --season 2022
xg:
	$(UV) run wcstrategy actions compute-xg --season 2022
xt:
	$(UV) run wcstrategy actions fit-xt --train-season 2018 --mode reference
	$(UV) run wcstrategy actions compute-xt --season 2022 --model reference
progression:
	$(UV) run wcstrategy actions compute-progression --season 2022
attacking-summary:
	$(UV) run wcstrategy actions build-attacking-summary --season 2022
milestone-2: actions xg xt progression attacking-summary
ppda:
	$(UV) run --no-sync wcstrategy pressure compute-ppda --season 2022
pressure-events:
	$(UV) run --no-sync wcstrategy pressure compute-events --season 2022
	$(UV) run --no-sync wcstrategy pressure build-sequences --season 2022
pressure-regains:
	$(UV) run --no-sync wcstrategy pressure compute-regains --season 2022
context360:
	$(UV) run --no-sync wcstrategy pressure compute-context360 --season 2022
pressure-summary:
	$(UV) run --no-sync wcstrategy pressure build-summary --season 2022
	$(UV) run --no-sync wcstrategy pressure validate --season 2022
milestone-3: ppda pressure-events pressure-regains context360 pressure-summary
