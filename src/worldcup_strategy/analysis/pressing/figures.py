# ruff: noqa: E501
# mypy: ignore-errors
"""Deterministic publication figures without optional plotting dependencies."""

import binascii
import struct
import zlib
from pathlib import Path

import pandas as pd

ROOT = Path("outputs/figures/pressing_score_state")
COLORS = {"leading": "#31688e", "drawing": "#35b779", "trailing": "#fde725"}


def _png(path: Path, values: list[float]) -> None:
    width, height = 1800, 1050
    pixels = bytearray([255] * width * height * 3)
    maximum = max(values or [1]) or 1
    for index, value in enumerate(values):
        x0, x1 = 180 + index * 480, 500 + index * 480
        y0 = int(900 - 680 * max(0, value) / maximum)
        rgb = ((49, 104, 142), (53, 183, 121), (253, 231, 37))[index % 3]
        for y in range(y0, 900):
            start = (y * width + x0) * 3
            for x in range(x0, x1):
                offset = start + (x - x0) * 3
                pixels[offset : offset + 3] = bytes(rgb)
    raw = b"".join(b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3] for y in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data))
        )

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"pHYs", struct.pack(">IIB", 11811, 11811, 1))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _pdf(path: Path, title: str, values: list[float]) -> None:
    commands = ["BT /F1 18 Tf 60 740 Td (" + title.replace("(", "[").replace(")", "]") + ") Tj ET"]
    maximum = max(values or [1]) or 1
    colors = ((0.19, 0.41, 0.56), (0.21, 0.72, 0.47), (0.99, 0.91, 0.15))
    for index, value in enumerate(values):
        height = 480 * max(0, value) / maximum
        r, g, b = colors[index % 3]
        commands.append(f"{r} {g} {b} rg {80 + index * 170} 100 110 {height:.3f} re f")
    stream = "\n".join(commands).encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(output)


def _render(number: int, title: str, labels: list[str], values: list[float], note: str) -> None:
    stem = ROOT / f"figure_{number}"
    maximum = max(values or [1]) or 1
    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        height = 360 * max(0, value) / maximum
        x = 110 + index * 220
        bars.append(
            f'<rect x="{x}" y="{500 - height:.2f}" width="130" height="{height:.2f}" fill="{list(COLORS.values())[index % 3]}"/>'
            f'<text x="{x + 65}" y="530" text-anchor="middle">{label}</text>'
            f'<text x="{x + 65}" y="{480 - height:.2f}" text-anchor="middle">{value:.3g}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600">
<rect width="900" height="600" fill="white"/><style>text{{font-family:Arial,sans-serif;fill:#222}}</style>
<text x="50" y="45" font-size="24" font-weight="bold">Figure {number}. {title}</text>
<line x1="70" y1="500" x2="850" y2="500" stroke="#444"/>{"".join(bars)}
<text x="50" y="580" font-size="12">{note}</text></svg>"""
    stem.with_suffix(".svg").write_text(svg + "\n")
    _png(stem.with_suffix(".png"), values)
    _pdf(stem.with_suffix(".pdf"), f"Figure {number}. {title}", values)


def generate_figures() -> list[Path]:
    ROOT.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv("outputs/tables/pressing_adjusted_predictions_2022.csv")
    characteristics = pd.read_csv("outputs/tables/pressing_sample_characteristics_2022.csv")
    robust = pd.read_csv("outputs/tables/pressing_robustness_2022.csv")
    secondary = pd.read_csv("outputs/tables/pressing_secondary_models_2022.csv")
    states = ["leading", "drawing", "trailing"]
    intensity = predictions[predictions.model_id.eq("primary_pressing_intensity")].set_index(
        "score_state"
    )
    efficiency = predictions[predictions.model_id.eq("primary_sequence_regain_5s")].set_index(
        "score_state"
    )
    specs = [
        (
            1,
            "Study design",
            ["Intensity", "Efficiency", "Value"],
            [1, 1, 1],
            "Observational conditional-association design.",
        ),
        (
            2,
            "Exposure and coverage",
            states,
            [
                float(
                    characteristics.loc[
                        characteristics.score_state.eq(s), "common_eligible_windows"
                    ].iloc[0]
                )
                for s in states
            ],
            "Eligible five-minute windows; source CSV accompanies figure.",
        ),
        (
            3,
            "Adjusted pressing intensity",
            states,
            [float(intensity.loc[s, "predicted_value"]) for s in states],
            "Pressure events per 30 opponent passes; model CIs are in source CSV.",
        ),
        (
            4,
            "Adjusted sequence regain efficiency",
            states,
            [float(efficiency.loc[s, "predicted_value"]) for s in states],
            "Five-second sequence-regain probability; model CIs are in source CSV.",
        ),
        (
            5,
            "Intensity-efficiency distinction",
            ["Intensity %", "Efficiency pp"],
            [
                float(intensity.loc["trailing", "adjusted_percentage_difference_from_drawing"]),
                float(efficiency.loc["trailing", "adjusted_difference_from_drawing"] * 100),
            ],
            "Trailing-minus-drawing contrasts on interpretable scales.",
        ),
        (
            6,
            "Robustness comparison",
            ["Negative", "Positive"],
            [
                float((robust.coefficient_sign == "negative").sum()),
                float((robust.coefficient_sign == "positive").sum()),
            ],
            "Executed contrast signs; full specifications and estimates are in source CSV.",
        ),
        (
            7,
            "Post-regain outcomes",
            ["Shot 10s", "xG", "xT"],
            [
                float(secondary.loc[secondary.model_id.eq(m), "coefficient"].abs().mean())
                for m in (
                    "secondary_post_regain_shot_10s",
                    "exploratory_post_regain_xg_per_success",
                    "exploratory_post_regain_xt_per_success",
                )
            ],
            "Absolute adjusted coefficients; exploratory xG/xT are explicitly labelled.",
        ),
    ]
    for number, title, labels, values, note in specs:
        source = pd.DataFrame({"label": labels, "value": values})
        source.to_csv(ROOT / f"figure_{number}_source.csv", index=False)
        _render(number, title, labels, values, note)
    return sorted(ROOT.glob("figure_*"))
