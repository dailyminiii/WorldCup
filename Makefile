UV := PYTHONPATH=src UV_CACHE_DIR=.uv-cache ./.tools/uv/uv

.PHONY: setup fetch-data validate-data build-data coverage test lint typecheck actions xg xt progression attacking-summary milestone-2 ppda pressure-events pressure-regains context360 pressure-summary milestone-3 state-windows state-segments state-features state-summaries state-models milestone-4
setup:
	$(UV) sync

fetch-data:
	$(UV) run --no-sync wcstrategy data fetch --season 2022

validate-data:
	$(UV) run --no-sync wcstrategy data validate --season 2022

build-data:
	$(UV) run --no-sync wcstrategy data build-canonical --season 2022

coverage:
	$(UV) run --no-sync wcstrategy data coverage --season 2022

test:
	$(UV) run --no-sync pytest

lint:
	$(UV) run --no-sync ruff check .
	$(UV) run --no-sync ruff format --check .

typecheck:
	$(UV) run --no-sync mypy src

actions:
	$(UV) run --no-sync wcstrategy actions build-spadl --season 2022
xg:
	$(UV) run --no-sync wcstrategy actions compute-xg --season 2022
xt:
	$(UV) run --no-sync wcstrategy actions fit-xt --train-season 2018 --mode reference
	$(UV) run --no-sync wcstrategy actions compute-xt --season 2022 --model reference
progression:
	$(UV) run --no-sync wcstrategy actions compute-progression --season 2022
attacking-summary:
	$(UV) run --no-sync wcstrategy actions build-attacking-summary --season 2022
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
state-windows:
	$(UV) run --no-sync wcstrategy state build-windows --season 2022 --window-minutes 5
state-segments:
	$(UV) run --no-sync wcstrategy state build-segments --season 2022
state-features:
	$(UV) run --no-sync wcstrategy state build-features --season 2022
state-summaries:
	$(UV) run --no-sync wcstrategy state summarize --season 2022
state-models:
	$(UV) run --no-sync wcstrategy state fit-models --season 2022
milestone-4: state-windows state-segments state-features state-summaries state-models
	$(UV) run --no-sync wcstrategy state validate --season 2022
