"""
Download iNaturalist observation metadata for mammals and birds.

Uses cursor-based pagination (id_above) for reliable large-scale downloads.
Saves incrementally to CSV as checkpoint.

Usage:
    python3 scripts/extraction/download_inaturalist.py [--taxon mammals|birds|both]
                                                      [--target 500000]
                                                      [--checkpoint-every 50]
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"

API_BASE = "https://api.inaturalist.org/v1/observations"
PER_PAGE = 200
RATE_LIMIT_DELAY = 0.61  # ~98 req/min, under the 100/min limit

TAXA = {
    "mammals": {
        "taxon_id": 40151,  # Mammalia
        "filename": "observations_mammals.csv",
    },
    "birds": {
        "taxon_id": 3,  # Aves
        "filename": "observations_birds.csv",
    },
}


def construct_medium_url(photo_url: str) -> str:
    """Convert square/thumbnail photo URL to medium resolution."""
    if "/square." in photo_url:
        return photo_url.replace("/square.", "/medium.")
    return photo_url


def extract_family(taxon: dict) -> str:
    """Try to extract family name from taxon data.

    The API doesn't directly return family in the observations endpoint.
    We store iconic_taxon_name as fallback and resolve families later
    via a separate taxonomy lookup.
    """
    if taxon is None:
        return "unknown"
    # iconic_taxon_name is just 'Mammalia' or 'Aves' at class level
    # We'll do a proper family lookup in post-processing
    return taxon.get("iconic_taxon_name", "unknown")


def fetch_page(
    taxon_id: int,
    id_above: int = 0,
    per_page: int = PER_PAGE,
    retries: int = 3,
) -> dict | None:
    """Fetch one page of observations from iNaturalist API."""
    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research",
        "photos": "true",
        "geo": "true",
        "order_by": "id",
        "order": "asc",
        "id_above": id_above,
        "per_page": per_page,
    }

    for attempt in range(retries):
        try:
            resp = requests.get(API_BASE, params=params, timeout=60)
            if resp.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            wait = 5 * (attempt + 1)
            print(f"  Error (attempt {attempt + 1}/{retries}): {e}, retrying in {wait}s")
            time.sleep(wait)

    return None


def parse_observation(obs: dict) -> dict | None:
    """Extract fields from a single observation."""
    obs_id = obs.get("id")
    if not obs_id:
        return None

    # Location
    loc = obs.get("location")
    if not loc:
        return None
    try:
        parts = loc.split(",")
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except (ValueError, IndexError):
        return None

    # Taxon
    taxon = obs.get("taxon") or {}
    species = taxon.get("name", "unknown")
    family = extract_family(taxon)
    common_name = taxon.get("preferred_common_name", "")

    # Date
    date = obs.get("observed_on") or ""

    # Photo URL (first photo, medium resolution)
    photos = obs.get("photos") or obs.get("observation_photos") or []
    if not photos:
        return None

    if isinstance(photos[0], dict) and "photo" in photos[0]:
        photo = photos[0]["photo"]
    elif isinstance(photos[0], dict) and "url" in photos[0]:
        photo = photos[0]
    else:
        return None

    photo_url = photo.get("url", "")
    if not photo_url:
        return None
    photo_url = construct_medium_url(photo_url)
    photo_id = photo.get("id", "")

    return {
        "observation_id": obs_id,
        "species": species,
        "common_name": common_name,
        "family": family,
        "lat": lat,
        "lon": lon,
        "date": date,
        "photo_url": photo_url,
        "photo_id": photo_id,
    }


def load_existing_ids(csv_path: Path) -> set:
    """Load already-downloaded observation IDs for resuming."""
    if not csv_path.exists():
        return set()
    ids = set()
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ids.add(int(row["observation_id"]))
            except (KeyError, ValueError):
                pass
    return ids


def load_last_id(csv_path: Path) -> int:
    """Get the last observation ID for cursor-based resume."""
    if not csv_path.exists():
        return 0
    last_id = 0
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                last_id = max(last_id, int(row["observation_id"]))
            except (KeyError, ValueError):
                pass
    return last_id


def download_observations(
    taxon_name: str,
    target: int = 500000,
    checkpoint_every: int = 50,
):
    """Download observation metadata for a taxon."""
    config = TAXA[taxon_name]
    taxon_id = config["taxon_id"]
    csv_path = DATA_VISION / config["filename"]

    # Resume support
    existing_ids = load_existing_ids(csv_path)
    id_above = load_last_id(csv_path)
    already = len(existing_ids)

    if already >= target:
        print(f"{taxon_name}: already have {already} >= target {target}, skipping")
        return

    print(f"{taxon_name}: have {already} observations, targeting {target}")
    print(f"  Resuming from id_above={id_above}")

    # Open CSV for appending
    file_exists = csv_path.exists()
    csvfile = open(csv_path, "a", newline="")
    fieldnames = [
        "observation_id",
        "species",
        "common_name",
        "family",
        "lat",
        "lon",
        "date",
        "photo_url",
        "photo_id",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    if not file_exists or already == 0:
        writer.writeheader()
        csvfile.flush()

    collected = 0
    page_num = 0
    consecutive_empty = 0
    t0 = time.time()

    try:
        while already + collected < target:
            page_num += 1
            data = fetch_page(taxon_id, id_above=id_above)
            if data is None:
                print(f"  Failed to fetch page {page_num}, stopping")
                break

            results = data.get("results", [])
            total = data.get("total_results", 0)

            if not results:
                consecutive_empty += 1
                if consecutive_empty >= 5:
                    print(f"  5 consecutive empty pages, stopping")
                    break
                continue

            consecutive_empty = 0
            new_in_page = 0
            max_id_this_page = id_above

            for obs in results:
                obs_id = obs.get("id", 0)
                max_id_this_page = max(max_id_this_page, obs_id)

                if obs_id in existing_ids:
                    continue

                parsed = parse_observation(obs)
                if parsed is None:
                    continue

                writer.writerow(parsed)
                existing_ids.add(obs_id)
                collected += 1
                new_in_page += 1

                if already + collected >= target:
                    break

            csvfile.flush()
            id_above = max_id_this_page

            # Progress
            elapsed = time.time() - t0
            rate = collected / elapsed if elapsed > 0 else 0
            total_done = already + collected
            eta = (target - total_done) / rate if rate > 0 else 0

            if page_num % 10 == 0 or new_in_page == 0:
                print(
                    f"  Page {page_num}: id>{id_above} | "
                    f"+{new_in_page} new | total {total_done}/{target} | "
                    f"{rate:.0f}/s | ETA {eta / 60:.0f}min | "
                    f"DB has {total:,} total"
                )

            # Checkpoint
            if page_num % checkpoint_every == 0:
                print(f"  [checkpoint] {total_done} observations saved to {csv_path.name}")

            time.sleep(RATE_LIMIT_DELAY)

    finally:
        csvfile.close()

    elapsed = time.time() - t0
    total_done = already + collected
    print(
        f"\n{taxon_name}: {collected} new observations downloaded "
        f"({total_done} total) in {elapsed / 60:.1f}min"
    )
    print(f"  Saved to {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Download iNaturalist observations")
    parser.add_argument(
        "--taxon",
        choices=["mammals", "birds", "both"],
        default="both",
        help="Which taxon to download (default: both)",
    )
    parser.add_argument(
        "--target",
        type=int,
        default=500000,
        help="Target observations per taxon (default: 500000)",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=50,
        help="Save checkpoint every N pages (default: 50)",
    )
    args = parser.parse_args()

    taxa = ["mammals", "birds"] if args.taxon == "both" else [args.taxon]

    for taxon in taxa:
        download_observations(taxon, args.target, args.checkpoint_every)


if __name__ == "__main__":
    main()
