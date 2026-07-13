"""Build the readable Markdown manuscript from generated LaTeX macros."""

import re
from pathlib import Path

PAPER = Path("paper/pressing_score_state")


def build_markdown() -> Path:
    """Substitute machine-generated values into the Markdown manuscript template."""
    macros = {}
    for name, value in re.findall(
        r"\\newcommand\{\\([A-Za-z]+)\}\{([^}]*)\}",
        (PAPER / "macros.tex").read_text(),
    ):
        macros[name] = value.replace("\\%", "%")
    template = (PAPER / "manuscript_draft_v1.template.md").read_text()
    missing = sorted(set(re.findall(r"\{\{([A-Za-z]+)\}\}", template)) - set(macros))
    if missing:
        raise ValueError(f"Missing generated manuscript macros: {missing}")
    for name, value in macros.items():
        template = template.replace("{{" + name + "}}", value)
    target = PAPER / "manuscript_draft_v1.md"
    target.write_text(template)
    return target


if __name__ == "__main__":
    print(build_markdown())
