"""Compare chaining and linear-probing search costs at equal load factors."""

import csv
import random
import string
import sys
from pathlib import Path
from typing import NamedTuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable

CAPACITY = 4093
SEED = 2026
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
TOKEN_CHARACTERS = string.ascii_lowercase + string.digits
CSV_COLUMNS = (
    "target_load_factor",
    "actual_load_factor",
    "entries",
    "chaining_success_measured",
    "chaining_success_theory",
    "chaining_failure_nodes_measured",
    "chaining_failure_nodes_theory",
    "linear_success_measured",
    "linear_success_theory",
    "linear_failure_nodes_measured",
    "linear_failure_nodes_theory",
)


class Result(NamedTuple):
    target_load: float
    actual_load: float
    entries: int
    chaining_success: float
    chaining_success_theory: float
    chaining_failure: float
    chaining_failure_theory: float
    linear_success: float
    linear_success_theory: float
    linear_failure: float
    linear_failure_theory: float


def _random_token(generator: random.Random, length: int = 16) -> str:
    return "".join(generator.choices(TOKEN_CHARACTERS, k=length))


def _make_urls(
    generator: random.Random, count: int, *, missing: bool = False
) -> list[str]:
    domain = "missing.invalid" if missing else "stored.example"
    return [
        f"https://{domain}/{_random_token(generator)}/{index}"
        for index in range(count)
    ]


def _average_probes(table: HashTable, urls: list[str], should_exist: bool) -> float:
    total_probes = 0
    for url in urls:
        value = table.get(url)
        if should_exist and value is None:
            raise RuntimeError(f"success-query URL was not inserted: {url}")
        if not should_exist and value is not None:
            raise RuntimeError(f"failure-query URL unexpectedly exists: {url}")
        total_probes += table.last_probes
    return total_probes / len(urls)


def collect_results() -> list[Result]:
    generator = random.Random(SEED)
    maximum_entries = round(CAPACITY * LOAD_FACTORS[-1])
    stored_urls = _make_urls(generator, maximum_entries)
    missing_urls = _make_urls(generator, maximum_entries, missing=True)
    results = []

    for target_load in LOAD_FACTORS:
        entry_count = round(CAPACITY * target_load)
        chaining = HashTable(capacity=CAPACITY, max_load=None)
        linear = LinearProbingHashTable(capacity=CAPACITY, max_load=None)
        for index in range(entry_count):
            key = stored_urls[index]
            value = str(index)
            chaining.put(key, value)
            linear.put(key, value)

        if chaining.capacity != CAPACITY or linear.capacity != CAPACITY:
            raise RuntimeError("an experiment table unexpectedly changed capacity")

        actual_load = chaining.load_factor
        if linear.load_factor != actual_load:
            raise RuntimeError("the two tables do not contain the same key count")

        success_urls = stored_urls[:entry_count]
        failure_urls = missing_urls[:entry_count]
        chaining_success = _average_probes(chaining, success_urls, should_exist=True)
        chaining_failure = _average_probes(chaining, failure_urls, should_exist=False)
        linear_success = _average_probes(linear, success_urls, should_exist=True)
        linear_failure = _average_probes(linear, failure_urls, should_exist=False)

        results.append(
            Result(
                target_load,
                actual_load,
                entry_count,
                chaining_success,
                1 + actual_load / 2,
                chaining_failure,
                actual_load,
                linear_success,
                0.5 * (1 + 1 / (1 - actual_load)),
                linear_failure,
                0.5 * (1 + 1 / (1 - actual_load) ** 2) - 1,
            )
        )

    return results


def write_csv(results: list[Result], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for result in results:
            writer.writerow(
                (
                    f"{result.target_load:.2f}",
                    f"{result.actual_load:.6f}",
                    result.entries,
                    f"{result.chaining_success:.6f}",
                    f"{result.chaining_success_theory:.6f}",
                    f"{result.chaining_failure:.6f}",
                    f"{result.chaining_failure_theory:.6f}",
                    f"{result.linear_success:.6f}",
                    f"{result.linear_success_theory:.6f}",
                    f"{result.linear_failure:.6f}",
                    f"{result.linear_failure_theory:.6f}",
                )
            )


def _draw_panel(
    svg: list[str],
    results: list[Result],
    *,
    left: int,
    title: str,
    y_max: float,
    y_ticks: tuple[int, ...],
    measured_chaining: str,
    theoretical_chaining: str,
    measured_linear: str,
    theoretical_linear: str,
) -> None:
    top, plot_width, plot_height = 110, 500, 420

    def x_position(load: float) -> float:
        return left + load * plot_width

    def y_position(probes: float) -> float:
        return top + plot_height - probes / y_max * plot_height

    svg.append(
        f'<text x="{left + plot_width / 2}" y="82" text-anchor="middle" '
        f'font-family="sans-serif" font-size="17">{title}</text>'
    )

    for tick in range(0, 11, 2):
        x = x_position(tick / 10)
        svg.extend(
            (
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#dddddd"/>',
                f'<text x="{x:.2f}" y="{top + plot_height + 22}" text-anchor="middle" font-family="sans-serif" font-size="12">{tick / 10:.1f}</text>',
            )
        )
    for tick in y_ticks:
        y = y_position(float(tick))
        svg.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>',
                f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick}</text>',
            )
        )

    svg.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222"/>',
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222"/>',
            f'<text x="{left + plot_width / 2}" y="{top + plot_height + 48}" text-anchor="middle" font-family="sans-serif" font-size="13">Load factor</text>',
        )
    )

    series = (
        (measured_chaining, "#1769aa", ""),
        (theoretical_chaining, "#1769aa", "7 4"),
        (measured_linear, "#d1495b", ""),
        (theoretical_linear, "#d1495b", "7 4"),
    )
    for value_name, color, dash in series:
        points = " ".join(
            f"{x_position(result.actual_load):.2f},{y_position(getattr(result, value_name)):.2f}"
            for result in results
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2.5"{dash_attribute}/>'
        )
        if not dash:
            for result in results:
                svg.append(
                    f'<circle cx="{x_position(result.actual_load):.2f}" '
                    f'cy="{y_position(getattr(result, value_name)):.2f}" '
                    f'r="3" fill="{color}"/>'
                )


def write_svg(results: list[Result], destination: Path) -> None:
    width, height = 1240, 690
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="620" y="32" text-anchor="middle" font-family="sans-serif" font-size="20">Chaining vs. linear probing</text>',
    ]
    _draw_panel(
        svg,
        results,
        left=80,
        title="Successful search comparisons",
        y_max=6,
        y_ticks=(0, 1, 2, 3, 4, 5, 6),
        measured_chaining="chaining_success",
        theoretical_chaining="chaining_success_theory",
        measured_linear="linear_success",
        theoretical_linear="linear_success_theory",
    )
    _draw_panel(
        svg,
        results,
        left=660,
        title="Unsuccessful search node comparisons",
        y_max=55,
        y_ticks=(0, 10, 20, 30, 40, 50),
        measured_chaining="chaining_failure",
        theoretical_chaining="chaining_failure_theory",
        measured_linear="linear_failure",
        theoretical_linear="linear_failure_theory",
    )

    legend = (
        ("Chaining: measured", "#1769aa", ""),
        ("Chaining: theory", "#1769aa", "7 4"),
        ("Linear probing: measured", "#d1495b", ""),
        ("Linear probing: theory", "#d1495b", "7 4"),
    )
    for index, (label, color, dash) in enumerate(legend):
        left = 80 + index * 285
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.extend(
            (
                f'<line x1="{left}" y1="635" x2="{left + 36}" y2="635" stroke="{color}" stroke-width="2.5"{dash_attribute}/>',
                f'<text x="{left + 44}" y="640" font-family="sans-serif" font-size="13">{label}</text>',
            )
        )
    svg.append("</svg>")
    destination.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    output_directory = Path(__file__).resolve().parent
    results = collect_results()
    csv_path = output_directory / "comparison_results.csv"
    svg_path = output_directory / "comparison_probes.svg"
    write_csv(results, csv_path)
    write_svg(results, svg_path)

    print(
        "alpha | n | chain success (meas/theory) | chain fail nodes (meas/theory) "
        "| linear success (meas/theory) | linear fail nodes (meas/theory)"
    )
    for result in results:
        print(
            f"{result.actual_load:.4f} | {result.entries:4d} | "
            f"{result.chaining_success:.3f}/{result.chaining_success_theory:.3f} | "
            f"{result.chaining_failure:.3f}/{result.chaining_failure_theory:.3f} | "
            f"{result.linear_success:.3f}/{result.linear_success_theory:.3f} | "
            f"{result.linear_failure:.3f}/{result.linear_failure_theory:.3f}"
        )
    print(f"\nWrote {csv_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
