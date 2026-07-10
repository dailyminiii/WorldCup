"""Command-line interface."""

from typing import Annotated

import typer

from worldcup_strategy.actions.pipeline import (
    build_attacking_2022,
    build_spadl_2022,
    compute_progression_2022,
    compute_xg_2022,
    compute_xt_2022,
    fit_xt,
)
from worldcup_strategy.config import load_data_config
from worldcup_strategy.data.downloader import fetch_repository
from worldcup_strategy.data.pipeline import build_canonical, validate_data, write_coverage
from worldcup_strategy.pressure.pipeline import (
    build_sequences_2022,
    build_summary_2022,
    compute_context_2022,
    compute_events_2022,
    compute_ppda_2022,
    compute_regains_2022,
    validate_2022,
)

app = typer.Typer(help="World Cup Strategy Lab reproducible research CLI.")
data_app = typer.Typer(help="Acquire, canonicalize, and validate provider data.")
app.add_typer(data_app, name="data")
actions_app = typer.Typer(help="Build action metrics and attacking summaries.")
app.add_typer(actions_app, name="actions")
pressure_app = typer.Typer(help="Build PPDA, Pressure, regain, and 360-context metrics.")
app.add_typer(pressure_app, name="pressure")


@pressure_app.command("compute-ppda")
def pressure_ppda(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"PPDA rows: {len(compute_ppda_2022())}")


@pressure_app.command("compute-events")
def pressure_events(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"Pressure events: {len(compute_events_2022())}")


@pressure_app.command("build-sequences")
def pressure_sequences(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"Pressure sequences: {len(build_sequences_2022())}")


@pressure_app.command("compute-regains")
def pressure_regains(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    regains, high, _ = compute_regains_2022()
    typer.echo(f"Pressure events evaluated: {len(regains)}; high regains: {len(high)}")


@pressure_app.command("compute-context360")
def pressure_context360(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"360 context rows: {len(compute_context_2022())}")


@pressure_app.command("build-summary")
def pressure_summary(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    match, tournament = build_summary_2022()
    typer.echo(f"Team-match rows: {len(match)}; teams: {len(tournament)}")


@pressure_app.command("validate")
def pressure_validate(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
) -> None:
    del competition, season
    typer.echo(json_summary(validate_2022()))


@actions_app.command("build-spadl")
def action_spadl(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"SPADL actions: {len(build_spadl_2022())}")


@actions_app.command("compute-xg")
def action_xg(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"Team-match xG rows: {len(compute_xg_2022())}")


@actions_app.command("fit-xt")
def action_fit_xt(
    train_competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    train_season: Annotated[int, typer.Option()] = 2018,
    mode: Annotated[str, typer.Option()] = "reference",
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del train_competition, train_season, force
    typer.echo(f"xT training actions: {fit_xt(mode)['training_action_count']}")


@actions_app.command("compute-xt")
def action_compute_xt(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    model: Annotated[str, typer.Option()] = "reference",
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"Action xT rows: {len(compute_xt_2022(model))}")


@actions_app.command("compute-progression")
def action_progression(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    typer.echo(f"Progression rows: {len(compute_progression_2022())}")


@actions_app.command("build-attacking-summary")
def action_summary(
    competition: Annotated[str, typer.Option()] = "FIFA World Cup",
    season: Annotated[int, typer.Option()] = 2022,
    force: Annotated[bool, typer.Option()] = False,
) -> None:
    del competition, season, force
    match, tournament = build_attacking_2022()
    typer.echo(f"Team-match rows: {len(match)}; teams: {len(tournament)}")


@data_app.command("fetch")
def fetch(season: Annotated[int, typer.Option()] = 2022) -> None:
    """Fetch or reuse the configured StatsBomb Open Data checkout."""
    config = load_data_config(season)
    manifest = fetch_repository(
        config.source_url, config.raw_repository, config.manifest_directory / "source.json"
    )
    typer.echo(f"StatsBomb source commit: {manifest['source_commit_sha']}")


@data_app.command("build-canonical")
def build(season: Annotated[int, typer.Option()] = 2022) -> None:
    """Build canonical Parquet tables."""
    counts = build_canonical(load_data_config(season))
    for name, count in counts.items():
        typer.echo(f"{name}: {count}")


@data_app.command("coverage")
def coverage(season: Annotated[int, typer.Option()] = 2022) -> None:
    """Generate Event and 360 coverage reports."""
    report = write_coverage(load_data_config(season))
    typer.echo(json_summary(report))


@data_app.command("validate")
def validate(season: Annotated[int, typer.Option()] = 2022) -> None:
    """Validate source completeness and processed constraints."""
    report = validate_data(load_data_config(season))
    typer.echo(json_summary(report))


def json_summary(report: dict[str, object]) -> str:
    """Render a compact stable CLI summary."""
    keys = (
        "match_count",
        "group_stage_match_count",
        "event_count",
        "three_sixty_match_count",
        "three_sixty_linked_event_count",
        "valid",
    )
    return "\n".join(f"{key}: {report[key]}" for key in keys if key in report)


if __name__ == "__main__":
    app()
