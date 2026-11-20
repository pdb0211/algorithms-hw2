"""Measure separate-chaining search probes at increasing load factors."""

import csv
import random
import string
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.hash_table import HashTable

CAPACITY = 4093
SEED = 2026
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
TOKEN_CHARACTERS = string.ascii_lowercase + string.digits
CSV_COLUMNS = (
    "target_load_factor",
    "actual_load_factor",
    "entries",
    "successful_avg_nodes",
    "successful_theory",
    "unsuccessful_avg_nodes",
    "unsuccessful_theory",
)


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


def _average_probes(table: HashTable, urls: list[str], *, expected_missing: bool) -> float:
    total_probes = 0
    for url in urls:
        value = table.get(url)
        if expected_missing and value is not None:
            raise RuntimeError(f"failure-query URL unexpectedly exists: {url}")
        if not expected_missing and value is None:
            raise RuntimeError(f"success-query URL was not inserted: {url}")
        total_probes += table.last_probes
    return total_probes / len(urls)


def collect_results() -> list[tuple[float, float, int, float, float, float, float]]:
    generator = random.Random(SEED)
    maximum_entries = int(CAPACITY * LOAD_FACTORS[-1])
    stored_urls = _make_urls(generator, maximum_entries)
    missing_urls = _make_urls(generator, maximum_entries, missing=True)
    results = []

    for target_load in LOAD_FACTORS:
        entry_count = round(CAPACITY * target_load)
        table = HashTable(capacity=CAPACITY, max_load=None)
        for index in range(entry_count):
            table.put(stored_urls[index], str(index))

        measured_load = table.load_factor
        successful_average = _average_probes(
            table, stored_urls[:entry_count], expected_missing=False
        )
        unsuccessful_average = _average_probes(
            table, missing_urls[:entry_count], expected_missing=True
        )
        results.append(
            (
                target_load,
                measured_load,
                entry_count,
                successful_average,
                1 + measured_load / 2,
                unsuccessful_average,
                measured_load,
            )
        )

    return results


def write_csv(
    results: list[tuple[float, float, int, float, float, float, float]],
    destination: Path,
) -> None:
    with destination.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for result in results:
            writer.writerow(
                (
                    f"{result[0]:.2f}",
                    f"{result[1]:.6f}",
                    result[2],
                    f"{result[3]:.6f}",
                    f"{result[4]:.6f}",
                    f"{result[5]:.6f}",
                    f"{result[6]:.6f}",
                )
            )


def write_svg(
    results: list[tuple[float, float, int, float, float, float, float]],
    destination: Path,
) -> None:
    width, height = 1180, 650
    left, top = 100, 55
    plot_width, plot_height = 800, 465
    x_max, y_max = 4.0, 5.0
    x_position = lambda load: left + load / x_max * plot_width
    y_position = lambda probes: top + plot_height - probes / y_max * plot_height
    lines = [
        (
            "Successful (measured)",
            3,
            "#1769aa",
            "",
        ),
        (
            "Successful (theory: 1 + alpha/2)",
            4,
            "#1769aa",
            "8 5",
        ),
        (
            "Unsuccessful (measured)",
            5,
            "#d1495b",
            "",
        ),
        (
            "Unsuccessful (theory: alpha)",
            6,
            "#d1495b",
            "8 5",
        ),
    ]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="590" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">Chaining hash table: measured and theoretical probes</text>',
    ]

    for load in range(5):
        x = x_position(float(load))
        svg.extend(
            (
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#dddddd"/>',
                f'<text x="{x:.2f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="sans-serif" font-size="13">{load}</text>',
            )
        )
    for probes in range(6):
        y = y_position(float(probes))
        svg.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>',
                f'<text x="{left - 14}" y="{y + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="13">{probes}</text>',
            )
        )

    svg.extend(
        (
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222"/>',
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 35}" text-anchor="middle" font-family="sans-serif" font-size="15">Load factor (alpha)</text>',
            f'<text x="25" y="{top + plot_height / 2}" transform="rotate(-90 25 {top + plot_height / 2})" text-anchor="middle" font-family="sans-serif" font-size="15">Average nodes compared</text>',
        )
    )

    for label, value_index, color, dash in lines:
        points = " ".join(
            f"{x_position(result[1]):.2f},{y_position(result[value_index]):.2f}"
            for result in results
        )
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"{dash_attribute}/>'
        )
        for result in results:
            svg.append(
                f'<circle cx="{x_position(result[1]):.2f}" cy="{y_position(result[value_index]):.2f}" r="3" fill="{color}"/>'
            )

    for index, (label, _, color, dash) in enumerate(lines):
        y = 110 + index * 30
        dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
        svg.extend(
            (
                f'<line x1="940" y1="{y}" x2="985" y2="{y}" stroke="{color}" stroke-width="2.5"{dash_attribute}/>',
                f'<text x="995" y="{y + 5}" font-family="sans-serif" font-size="13">{label}</text>',
            )
        )

    svg.append("</svg>")
    destination.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    output_directory = Path(__file__).resolve().parent
    csv_path = output_directory / "results.csv"
    svg_path = output_directory / "probes.svg"
    results = collect_results()
    write_csv(results, csv_path)
    write_svg(results, svg_path)

    print(
        "target α | actual α | entries | successful (measured / theory) "
        "| unsuccessful (measured / theory)"
    )
    for result in results:
        print(
            f"{result[0]:8.2f} | {result[1]:8.4f} | {result[2]:7d} | "
            f"{result[3]:8.4f} / {result[4]:8.4f} | "
            f"{result[5]:10.4f} / {result[6]:8.4f}"
        )
    print(f"\nWrote {csv_path}")
    print(f"Wrote {svg_path}")


if __name__ == "__main__":
    main()
