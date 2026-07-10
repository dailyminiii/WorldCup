"""Command-line interface."""

from typing import Annotated

import typer

from worldcup_strategy.config import load_data_config
from worldcup_strategy.data.downloader import fetch_repository
from worldcup_strategy.data.pipeline import build_canonical, validate_data, write_coverage

app = typer.Typer(help="World Cup Strategy Lab reproducible research CLI.")
data_app = typer.Typer(help="Acquire, canonicalize, and validate provider data.")
app.add_typer(data_app, name="data")


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
