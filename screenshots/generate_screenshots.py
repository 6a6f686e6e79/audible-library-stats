"""Generate dashboard screenshots using a fictional library fixture.

Writes a fake audible_data.json (entirely invented titles/authors — no real
listening data), launches the Streamlit app, and captures per-tab screenshots.

Re-run any time with:
    python screenshots/generate_screenshots.py
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"
DATA_PATH = ROOT / "audible_data.json"
BACKUP_PATH = ROOT / "audible_data.json.bak"
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/"
VIEWPORT = {"width": 1440, "height": 1000}

# Fictional library — invented titles and author names. No relation to any
# real catalog. Runtimes in minutes, dates as ISO strings.
FAKE_BOOKS = [
    ("The Cartographer's Atlas",     "Anne Marsh",        1284, 100,  True,  "2018-03-14", "2018-04-02"),
    ("Quiet Stations",               "Daniel Okafor",      612, 100,  True,  "2018-06-21", "2018-07-10"),
    ("A Theory of Small Engines",    "Priya Raman",        892,  73,  False, "2018-09-02", ""),
    ("The Salt Lantern",             "Cleo Vandermeer",   1455, 100,  True,  "2019-01-11", "2019-02-08"),
    ("Notes From the Long Hallway",  "Idris Bell",         421, 100,  True,  "2019-03-22", "2019-04-01"),
    ("Drift, Then Anchor",           "Mira Saito",         756,   0,  False, "2019-05-30", ""),
    ("How the Forest Counts",        "Owen Mackey",        980,  45,  False, "2019-07-04", ""),
    ("The Last Telegram Office",     "Sasha Lindqvist",   1132, 100,  True,  "2019-09-18", "2019-10-29"),
    ("Bright Migrations",            "Theo Adesanya",      642,  92,  False, "2020-01-07", ""),
    ("On Inventing Mondays",         "Rosa Kapur",         378, 100,  True,  "2020-02-14", "2020-02-22"),
    ("Riverstone, Probably",         "Joaquin Velez",      812,   0,  False, "2020-04-03", ""),
    ("A Field Guide to Almosts",     "Hattie Brooks",      594, 100,  True,  "2020-06-19", "2020-07-04"),
    ("The Index of Borrowed Light",  "Felix Tanaka",      1820,  31,  False, "2020-08-25", ""),
    ("Walking the Slow Wire",        "Naomi Pereira",      702, 100,  True,  "2020-10-11", "2020-11-08"),
    ("Departures, Annotated",        "Caspian Lowell",     488,  64,  False, "2020-12-02", ""),
    ("Eleven Provinces of Sleep",    "Lila Achterberg",   1350, 100,  True,  "2021-01-19", "2021-03-05"),
    ("How to Read a Coastline",      "Hugo Marin",         556, 100,  True,  "2021-02-28", "2021-03-21"),
    ("The Apprentice's Compass",     "Yara Solberg",       948,  18,  False, "2021-04-12", ""),
    ("Northbound, in Pieces",        "Edwin Park",         674, 100,  True,  "2021-05-23", "2021-06-14"),
    ("Sunday Mechanics",             "Aisha Devereaux",    402,   0,  False, "2021-07-06", ""),
    ("The Mapmaker's Apology",       "Anne Marsh",        1190, 100,  True,  "2021-08-17", "2021-09-29"),
    ("Light Industry of the Heart",  "Marcus Holloway",    768,  95,  False, "2021-10-04", ""),
    ("Songs the Roof Knows",         "Vesna Karadzic",     521, 100,  True,  "2021-11-21", "2021-12-12"),
    ("The Distance Between Verbs",   "Quentin Abara",      864,  52,  False, "2022-01-08", ""),
    ("Catalog of Small Returns",     "Priya Raman",        612, 100,  True,  "2022-02-16", "2022-03-04"),
    ("Westerlies, A Memoir",         "Ingrid Halvorsen",  1040, 100,  True,  "2022-04-02", "2022-05-19"),
    ("The Glassblower's Holiday",    "Theo Adesanya",      588,   0,  False, "2022-05-22", ""),
    ("Halfway to Always",            "Romy Banerjee",      714, 100,  True,  "2022-07-09", "2022-08-01"),
    ("Stations of Almost",           "Jonas Vinter",       928,  41,  False, "2022-08-14", ""),
    ("The Quiet Architectures",      "Cleo Vandermeer",   1278, 100,  True,  "2022-10-03", "2022-11-22"),
    ("Notes Toward a Wider River",   "Tamsin Yost",        496, 100,  True,  "2022-11-19", "2022-12-08"),
    ("The Knot Tier's Daughter",     "Roman Ishikawa",     802,  78,  False, "2023-01-15", ""),
    ("Postcards From Verge",         "Nadia Eberhart",     558, 100,  True,  "2023-02-26", "2023-03-15"),
    ("How the Birds Vote",           "Owen Mackey",        648,   0,  False, "2023-04-04", ""),
    ("A Brief History of Maybe",     "Solenne Tritt",      882, 100,  True,  "2023-05-12", "2023-06-19"),
    ("The Engineer Who Forgot Wind", "Felix Tanaka",      1620, 100,  True,  "2023-06-28", "2023-08-22"),
    ("Migration Without a Map",      "Idris Bell",         492,  84,  False, "2023-07-30", ""),
    ("Hours Owed to Rain",           "Mira Saito",         726, 100,  True,  "2023-09-11", "2023-10-04"),
    ("On Being Briefly Famous",      "Caspian Lowell",     354,   0,  False, "2023-10-25", ""),
    ("The Lighthouse Bookkeeper",    "Hattie Brooks",      988, 100,  True,  "2023-11-30", "2024-01-21"),
    ("A Grammar of Departures",      "Quentin Abara",      612,  91,  False, "2024-01-08", ""),
    ("Slow Inventions",              "Rosa Kapur",         448, 100,  True,  "2024-02-20", "2024-03-08"),
    ("The Borrowed Mountain",        "Anne Marsh",        1392,  22,  False, "2024-03-29", ""),
    ("Letters to a Closed Bridge",   "Daniel Okafor",      584, 100,  True,  "2024-05-06", "2024-06-02"),
    ("The Long, Unhurried Sentence", "Sasha Lindqvist",    872,   0,  False, "2024-06-18", ""),
    ("Catalog of Doorways",          "Naomi Pereira",      660, 100,  True,  "2024-08-04", "2024-09-12"),
    ("How to Build a Smaller House", "Marcus Holloway",    498,  67,  False, "2024-09-22", ""),
    ("Echoes, Reasonably",           "Yara Solberg",       742, 100,  True,  "2024-11-01", "2024-12-19"),
    ("On the Patience of Bridges",   "Vesna Karadzic",     396,   0,  False, "2025-01-14", ""),
    ("The Letterpress Apprentice",   "Edwin Park",         824,  39,  False, "2025-03-02", ""),
]


def build_fixture():
    """Return a fake audible_data.json structure shaped like the real API output."""
    library = []
    for i, (title, author, runtime_min, pct, finished, purchased, finished_at) in enumerate(FAKE_BOOKS):
        library.append({
            "asin": f"FAKE{i:04d}A",
            "title": title,
            "authors": [{"name": author}],
            "runtime_length_min": runtime_min,
            "percent_complete": pct,
            "is_finished": finished,
            "purchase_date": f"{purchased}T12:00:00Z",
            "listening_status": {
                "finished_at_timestamp": f"{finished_at}T12:00:00Z" if finished_at else ""
            },
        })

    total_listened_ms = sum(
        int((b["runtime_length_min"] * 60 * 1000) * (b["percent_complete"] / 100))
        for b in library
    )

    return {
        "library": library,
        "total_stats": {
            "aggregated_total_listening_stats": {"aggregated_sum": total_listened_ms}
        },
        "finished": [],
        "wishlist": [],
        "account": {},
    }


def wait_for_port(host, port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.4)
    return False


def main():
    # Stage fixture (back up any existing real data first).
    had_existing = DATA_PATH.exists()
    if had_existing:
        shutil.copy2(DATA_PATH, BACKUP_PATH)

    DATA_PATH.write_text(json.dumps(build_fixture(), indent=2))
    print(f"Wrote fixture to {DATA_PATH}")

    streamlit_proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "audible_app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not wait_for_port("127.0.0.1", PORT, timeout=45):
            raise RuntimeError("Streamlit did not start in time")
        # Give Streamlit a moment to finish first render after the port opens.
        time.sleep(2.0)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
            page = ctx.new_page()
            page.goto(URL, wait_until="networkidle")
            page.wait_for_selector("text=Audible Library Dashboard", timeout=15000)
            page.wait_for_timeout(1200)

            def shoot(name):
                path = OUT / f"{name}.png"
                page.screenshot(path=str(path), full_page=False)
                print(f"wrote {path}")

            def click_tab(label):
                page.locator(f'button[role="tab"]:has-text("{label}")').click()
                page.wait_for_timeout(1800)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(400)

            # --- Standard viewport: focused per-tab shots ---
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)
            shoot("01-library")

            click_tab("Charts")
            shoot("02-charts")

            click_tab("Deep Dive")
            # Pick an author with multiple books for a more interesting view.
            # Open the "Select an author" combobox inside the Deep Dive tab
            # (label-scoped so we don't hit the sidebar's author multiselect).
            page.get_by_label("Select an author").click()
            page.wait_for_timeout(400)
            page.keyboard.type("Anne Marsh")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.wait_for_timeout(900)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            shoot("03-deep-dive")

            # --- Tall viewport: full-page shots that fit all sections ---
            page.set_viewport_size({"width": 1440, "height": 2600})
            page.wait_for_timeout(800)

            click_tab("Library")
            shoot("00-overview-full")

            click_tab("Charts")
            # Scroll the page to force lazy charts (Vega) to render, then back to top.
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(600)
            shoot("02-charts-full")

            click_tab("Deep Dive")
            # Open the "Select an author" combobox inside the Deep Dive tab
            # (label-scoped so we don't hit the sidebar's author multiselect).
            page.get_by_label("Select an author").click()
            page.wait_for_timeout(400)
            page.keyboard.type("Anne Marsh")
            page.wait_for_timeout(400)
            page.keyboard.press("Enter")
            page.wait_for_timeout(900)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(600)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)
            shoot("03-deep-dive-full")

            browser.close()
    finally:
        streamlit_proc.terminate()
        try:
            streamlit_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_proc.kill()

        # Restore prior data (or remove our fixture if none existed).
        if had_existing:
            shutil.move(str(BACKUP_PATH), str(DATA_PATH))
            print(f"Restored prior {DATA_PATH}")
        else:
            try:
                DATA_PATH.unlink()
            except FileNotFoundError:
                pass
            print(f"Removed fixture {DATA_PATH}")


if __name__ == "__main__":
    main()
