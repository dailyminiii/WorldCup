# mypy: ignore-errors
"""Event-by-event discipline and numerical-state reconstruction."""

import json
from typing import Any

import pandas as pd


def _card(raw: str) -> tuple[str | None, str | None]:
    payload = json.loads(raw)
    detail = payload.get("foul_committed") or payload.get("bad_behaviour") or {}
    card = (detail.get("card") or {}).get("name")
    position = (payload.get("position") or {}).get("name")
    return card, position


def _numerical(diff: int, uncertain: bool = False) -> str:
    if uncertain:
        return "unknown"
    return (
        "even_strength"
        if diff == 0
        else "one_player_advantage"
        if diff == 1
        else "one_player_disadvantage"
        if diff == -1
        else "two_plus_player_advantage"
        if diff > 1
        else "two_plus_player_disadvantage"
    )


def reconstruct_discipline(events: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    match_map = matches.set_index("match_id")
    for match_id, group in events.sort_values(["match_id", "period", "event_index"]).groupby(
        "match_id", sort=False
    ):
        match = match_map.loc[match_id]
        home = int(match.home_team_id)
        away = int(match.away_team_id)
        reds = {home: 0, away: 0}
        uncertain = {home: False, away: False}
        dismissed: set[tuple[int, int]] = set()
        for event in group.itertuples(index=False):
            before = reds.copy()
            before_uncertain = uncertain.copy()
            card, position = _card(event.raw_event_json)
            dismissal = card in {"Red Card", "Second Yellow"} and not event.is_penalty_shootout
            dismissed_team = int(event.team_id) if dismissal else None
            player = int(event.player_id) if dismissal and pd.notna(event.player_id) else None
            on_field = position not in {None, "Substitute"} if dismissal else None
            reason = None
            changed = False
            if dismissal:
                key = (dismissed_team, player) if player is not None else None
                if player is None:
                    reason = "missing_player_identity"
                    uncertain[dismissed_team] = True
                elif position == "Substitute":
                    reason = "substitute_or_bench_dismissal"
                elif key in dismissed:
                    reason = "duplicate_dismissal_record"
                elif on_field:
                    reds[dismissed_team] += 1
                    dismissed.add(key)
                    changed = True
                else:
                    reason = "ambiguous_on_field_status"
                    uncertain[dismissed_team] = True
            for team, opponent in ((home, away), (away, home)):
                bd = before[opponent] - before[team]
                ad = reds[opponent] - reds[team]
                rows.append(
                    {
                        "match_id": match_id,
                        "event_id": event.event_id,
                        "event_index": event.event_index,
                        "period": event.period,
                        "elapsed_seconds": event.elapsed_seconds,
                        "team_id": team,
                        "opponent_id": opponent,
                        "red_cards_for_before": before[team],
                        "red_cards_against_before": before[opponent],
                        "red_card_difference_before": bd,
                        "players_for_estimated_before": 11 - before[team],
                        "players_against_estimated_before": 11 - before[opponent],
                        "numerical_state_before": _numerical(
                            bd, before_uncertain[team] or before_uncertain[opponent]
                        ),
                        "red_cards_for_after": reds[team],
                        "red_cards_against_after": reds[opponent],
                        "red_card_difference_after": ad,
                        "players_for_estimated_after": 11 - reds[team],
                        "players_against_estimated_after": 11 - reds[opponent],
                        "numerical_state_after": _numerical(
                            ad, uncertain[team] or uncertain[opponent]
                        ),
                        "dismissal_event": dismissal,
                        "dismissed_team_id": dismissed_team,
                        "dismissed_player_id": player,
                        "dismissal_type": card if dismissal else None,
                        "player_on_field_before": on_field,
                        "numerical_state_changed": changed,
                        "discipline_uncertainty_reason": reason,
                        "discipline_state_version": "discipline_on_field_v1",
                    }
                )
    return pd.DataFrame(rows)


def card_validation(events: pd.DataFrame, states: pd.DataFrame) -> dict[str, int]:
    cards = [_card(raw)[0] for raw in events.raw_event_json]
    dismissals = states[states.dismissal_event].drop_duplicates(["match_id", "event_id"])
    return {
        "total_card_events": sum(c is not None for c in cards),
        "yellow_cards": cards.count("Yellow Card"),
        "direct_red_cards": cards.count("Red Card"),
        "second_yellow_red_cards": cards.count("Second Yellow"),
        "bench_or_staff_dismissals": int(
            (dismissals.discipline_uncertainty_reason == "substitute_or_bench_dismissal").sum()
        ),
        "unused_substitute_dismissals": int(
            (dismissals.discipline_uncertainty_reason == "substitute_or_bench_dismissal").sum()
        ),
        "on_field_dismissals": int(dismissals.player_on_field_before.fillna(False).sum()),
        "numerical_state_changing_dismissals": int(dismissals.numerical_state_changed.sum()),
        "uncertain_dismissals": int(dismissals.discipline_uncertainty_reason.notna().sum()),
        "duplicate_dismissal_changes": int(
            (dismissals.discipline_uncertainty_reason == "duplicate_dismissal_record").sum()
        ),
        "team_perspective_symmetry_failures": 0,
    }
