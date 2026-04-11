"""
Download iNaturalist images from observation CSVs.

Downloads medium-resolution photos concurrently.
Supports resume (skips already-downloaded images).

Usage:
    python3 scripts/extraction/download_inaturalist_images.py [--taxon mammals|birds|both]
                                                             [--max-images 500000]
                                                             [--workers 16]
"""

import argparse
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"

TIMEOUT = 30
MAX_RETRIES = 3


def download_image(url: str, dest: Path) -> bool:
    """Download a single image with retries."""
    if dest.exists() and dest.stat().st_size > 1000:
        return True  # already downloaded

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=TIMEOUT, stream=True)
            if resp.status_code == 404:
                return False  # image removed
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            resp.raise_for_status()

            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file is not empty/corrupt
            if dest.stat().st_size < 500:
                dest.unlink()
                return False

            return True

        except (requests.RequestException, OSError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 * (attempt + 1))
            continue

    return False


def get_existing_images(image_dir: Path) -> set:
    """Set of observation IDs that already have images downloaded."""
    existing = set()
    if not image_dir.exists():
        return existing
    for f in image_dir.glob("*.jpg"):
        try:
            obs_id = int(f.stem)
            existing.add(obs_id)
        except ValueError:
            pass
    return existing


def download_taxon_images(
    taxon: str,
    max_images: int = 500000,
    workers: int = 16,
):
    """Download images for one taxon."""
    csv_path = DATA_VISION / f"observations_{taxon}.csv"
    image_dir = DATA_VISION / "images" / taxon

    if not csv_path.exists():
        print(f"{csv_path} not found, skipping {taxon}")
        return

    image_dir.mkdir(parents=True, exist_ok=True)

    # Load observations
    obs_list = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obs_list.append(row)
            if len(obs_list) >= max_images:
                break

    print(f"{taxon}: {len(obs_list)} observations to process")

    # Filter to those not yet downloaded
    existing = get_existing_images(image_dir)
    to_download = []
    for row in obs_list:
        try:
            obs_id = int(row["observation_id"])
        except (KeyError, ValueError):
            continue
        if obs_id not in existing:
            to_download.append(row)

    print(f"  Already have {len(existing)} images, need to download {len(to_download)}")

    if not to_download:
        print(f"  All images already downloaded, nothing to do")
        return

    # Download concurrently
    downloaded = 0
    failed = 0
    t0 = time.time()

    def process_one(row):
        obs_id = row["observation_id"]
        url = row.get("photo_url", "")
        if not url:
            return False, "no_url"
        dest = image_dir / f"{obs_id}.jpg"
        ok = download_image(url, dest)
        return ok, obs_id

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_one, row): row for row in to_download}

        for i, future in enumerate(as_completed(futures)):
            ok, obs_id = future.result()
            if ok:
                downloaded += 1
            else:
                failed += 1

            # Progress every 500
            if (downloaded + failed) % 500 == 0:
                elapsed = time.time() - t0
                rate = (downloaded + failed) / elapsed if elapsed > 0 else 0
                done = downloaded + failed
                total = len(to_download)
                print(
                    f"  {done}/{total} ({100 * done / total:.0f}%) | "
                    f"{downloaded} ok, {failed} fail | "
                    f"{rate:.0f}/s | {elapsed / 60:.1f}min"
                )

    elapsed = time.time() - t0
    print(f"\n{taxon}: {downloaded} downloaded, {failed} failed in {elapsed / 60:.1f}min")
    print(f"  Images in {image_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download iNaturalist images")
    parser.add_argument(
        "--taxon",
        choices=["mammals", "birds", "both"],
        default="both",
    )
    parser.add_argument("--max-images", type=int, default=500000)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    taxa = ["mammals", "birds"] if args.taxon == "both" else [args.taxon]

    for taxon in taxa:
        download_taxon_images(taxon, args.max_images, args.workers)


if __name__ == "__main__":
    main()
