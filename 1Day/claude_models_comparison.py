"""Simple module to demonstrate the differences between Claude models.

This module provides a compact comparison of Claude Opus, Claude Sonnet,
and Claude Haiku for educational and demo purposes.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ClaudeModel:
    name: str
    best_for: str
    strength: str
    speed: str
    cost: str
    quality: str
    note: str


def get_models() -> List[ClaudeModel]:
    """Return a list of Claude model profiles for comparison."""
    return [
        ClaudeModel(
            name="Claude Opus",
            best_for="Complex reasoning, deep analysis, high-stakes tasks",
            strength="Highest quality and nuance",
            speed="Slower",
            cost="Highest",
            quality="Excellent",
            note="Best when accuracy and depth matter more than speed.",
        ),
        ClaudeModel(
            name="Claude Sonnet",
            best_for="Balanced everyday coding and general work",
            strength="Great mix of quality and speed",
            speed="Balanced",
            cost="Medium",
            quality="Very strong",
            note="A strong default choice for most production scenarios.",
        ),
        ClaudeModel(
            name="Claude Haiku",
            best_for="Fast, lightweight, and low-cost tasks",
            strength="Fastest response with lower latency",
            speed="Fastest",
            cost="Lowest",
            quality="Good",
            note="Best for simple automation, chat, and high-volume workloads.",
        ),
    ]


def compare_models() -> str:
    """Create a readable comparison summary for all Claude models."""
    models = get_models()
    lines = [
        "Claude Model Comparison",
        "=======================",
    ]

    for model in models:
        lines.append(f"\n{model.name}")
        lines.append(f"- Best for: {model.best_for}")
        lines.append(f"- Strength: {model.strength}")
        lines.append(f"- Speed: {model.speed}")
        lines.append(f"- Cost: {model.cost}")
        lines.append(f"- Quality: {model.quality}")
        lines.append(f"- Note: {model.note}")

    lines.append("\nQuick rule of thumb:")
    lines.append("- Choose Opus for the hardest reasoning tasks.")
    lines.append("- Choose Sonnet for a balanced everyday default.")
    lines.append("- Choose Haiku for speed and budget-sensitive use cases.")

    lines.append("\n Use case example:")
    lines.append("- Scenario: You have a 2-page product brief and need a launch plan.")
    lines.append("  * Claude Opus: best for a detailed, accurate implementation plan with")
    lines.append("    strong reasoning and nuance.")
    lines.append("  * Claude Sonnet: best for a solid plan with good speed and reliable")
    lines.append("    structure.")
    lines.append("  * Claude Haiku: best for a fast outline or quick checklist when you")
    lines.append("    want a lightweight result.")

    return "\n".join(lines)


if __name__ == "__main__":
    print(compare_models())
