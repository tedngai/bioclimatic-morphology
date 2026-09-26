#!/usr/bin/env python3
"""Segment animal subjects in iNaturalist photos with SAM 3 (open-vocabulary text prompts).

For each photo, SAM 3 is prompted with the subject's common name (or species/taxon) and the
top-scoring segmentation mask is saved as a binary PNG. A manifest row records the bbox,
score, and mask-area fraction so the training dataset can later produce full-frame /
bbox-crop / background-masked image variants for the morphology experiment
(full-frame vs. segmented comparison under the same species-disjoint split).

Outputs:
  {out_dir}/masks/{taxon}/{observation_id}.png      binary mask (0/255), original resolution
  {out_dir}/manifest.csv                            one row per processed image (append-safe)

Resume: rows whose observation_id is already in manifest.csv are skipped.

Environment: run with the `sam3` conda env (torch 2.12+cu130, sam3 package).
  /home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py ...

Examples:
  # Pilot: 1000 mammals, batch 8
  sam3-python segment_sam3.py --taxon mammals --batch-size 8 --limit 1000

  # Full run
  sam3-python segment_sam3.py --taxon both --batch-size 8

  # Once the HF checkpoint is downloaded locally (avoids re-fetching):
  sam3-python segment_sam3.py --taxon both --checkpoint ~/.cache/.../sam3.pt
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from tqdm import tqdm

from sam3.model_builder import build_sam3_image_model
from sam3.eval.postprocessors import PostProcessImage
from sam3.model.utils.misc import copy_data_to_device
from sam3.train.data.collator import collate_fn_api as collate
from sam3.train.data.sam3_image_dataset import (
    Datapoint,
    FindQueryLoaded,
    Image as SAMImage,
    InferenceMetadata,
)
from sam3.train.transforms.basic_for_api import (
    ComposeAPI,
    NormalizeAPI,
    RandomResizeAPI,
    ToTensorAPI,
)

MANIFEST_FIELDS = [
    "observation_id", "taxon", "species", "common_name", "image_path", "mask_path",
    "prompt", "has_detection", "score", "bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1",
    "mask_area_fraction", "error",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", type=Path, default=Path("data/vision/train_all.csv"))
    p.add_argument("--out-dir", type=Path, default=Path("data/vision/segmented"))
    p.add_argument("--taxon", choices=["mammals", "birds", "both"], default="both")
    p.add_argument("--prompt-field", choices=["common_name", "species", "taxon"], default="common_name")
    p.add_argument("--fallback-field", choices=["common_name", "species", "taxon", "none"], default="taxon",
                   help="secondary prompt tried when the primary yields no detection")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--resolution", type=int, default=1008)
    p.add_argument("--confidence-threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=None, help="process only this many images (pilot)")
    p.add_argument("--checkpoint", type=Path, default=None, help="local sam3.pt path (skip HF download)")
    p.add_argument("--image-root", type=Path, default=None,
                   help="base dir for relative image_path (default: the CSV's parent dir)")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--dtype", choices=["bfloat16", "float16", "float32"], default="bfloat16")
    p.add_argument("--flush-every", type=int, default=50, help="flush manifest every N batches")
    return p.parse_args()


def build_transform(resolution: int) -> ComposeAPI:
    return ComposeAPI(transforms=[
        RandomResizeAPI(sizes=resolution, max_size=resolution, square=True, consistent_transform=False),
        ToTensorAPI(),
        NormalizeAPI(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])


def make_datapoint(pil_image: Image.Image, prompt: str, query_id: int) -> Datapoint:
    w, h = pil_image.size
    dp = Datapoint(find_queries=[], images=[])
    dp.images = [SAMImage(data=pil_image, objects=[], size=[h, w])]
    dp.find_queries.append(
        FindQueryLoaded(
            query_text=prompt,
            image_id=0,
            object_ids_output=[],
            is_exhaustive=True,
            query_processing_order=0,
            inference_metadata=InferenceMetadata(
                coco_image_id=query_id,
                original_image_id=query_id,
                original_category_id=1,
                original_size=[h, w],
                object_id=0,
                frame_index=0,
            ),
        )
    )
    return dp


def load_done(out_dir: Path) -> set[str]:
    manifest = out_dir / "manifest.csv"
    done: set[str] = set()
    if manifest.exists():
        for row in csv.DictReader(manifest.open()):
            done.add(row["observation_id"])
    return done


def open_manifest(out_dir: Path):
    manifest = out_dir / "manifest.csv"
    write_header = not manifest.exists()
    f = manifest.open("a", newline="")
    writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
    if write_header:
        writer.writeheader()
    return f, writer


def to_cpu_numpy(x) -> np.ndarray:
    if isinstance(x, torch.Tensor):
        return x.detach().to("cpu", torch.float32).numpy()
    return np.asarray(x)


def best_mask_from_result(result: dict):
    """Return (mask[H,W] bool, score float, bbox xyxy) for the top detection, or None."""
    scores = to_cpu_numpy(result.get("scores", np.empty(0))).reshape(-1)
    if scores.size == 0:
        return None
    best = int(np.argmax(scores))
    score = float(scores[best])
    masks = result.get("masks")
    if masks is None:
        return None
    m = masks[best]
    m = to_cpu_numpy(m)
    mask_bool = m > 0.5
    boxes = to_cpu_numpy(result.get("boxes", np.empty((0, 4)))).reshape(-1, 4)
    bbox = boxes[best].tolist() if boxes.shape[0] > best else [0.0, 0.0, 0.0, 0.0]
    return mask_bool, score, bbox


def save_mask(mask_bool: np.ndarray, taxon: str, obs_id: str, out_dir: Path) -> Path:
    mask_dir = out_dir / "masks" / taxon
    mask_dir.mkdir(parents=True, exist_ok=True)
    path = mask_dir / f"{obs_id}.png"
    Image.fromarray((mask_bool.astype(np.uint8) * 255), mode="L").save(path, optimize=True)
    return path


def row_from(obs, mask_path, prompt, has_det, score, bbox, area_frac, error=""):
    return {
        "observation_id": obs["observation_id"],
        "taxon": obs["taxon"],
        "species": obs["species"],
        "common_name": obs["common_name"],
        "image_path": obs["image_path"],
        "mask_path": str(mask_path) if mask_path else "",
        "prompt": prompt,
        "has_detection": int(has_det),
        "score": f"{score:.4f}" if score is not None else "",
        "bbox_x0": f"{bbox[0]:.1f}" if bbox else "",
        "bbox_y0": f"{bbox[1]:.1f}" if bbox else "",
        "bbox_x1": f"{bbox[2]:.1f}" if bbox else "",
        "bbox_y1": f"{bbox[3]:.1f}" if bbox else "",
        "mask_area_fraction": f"{area_frac:.4f}" if area_frac is not None else "",
        "error": error,
    }


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    image_root = args.image_root if args.image_root is not None else args.csv.parent

    def resolve_image_path(p: str) -> str:
        pp = Path(p)
        return str(pp if pp.is_absolute() else image_root / pp)

    # --- Data ---
    df = pd.read_csv(args.csv, low_memory=False)
    if args.taxon != "both":
        df = df[df["taxon"] == args.taxon].copy()
    df = df[df["image_path"].notna()].copy()
    df = df.drop_duplicates(subset="observation_id").reset_index(drop=True)

    done = load_done(args.out_dir)
    df = df[~df["observation_id"].isin(done)].reset_index(drop=True)
    if args.limit:
        df = df.head(args.limit)
    print(f"[segment_sam3] {len(df)} images to process ({len(done)} already done)")

    if len(df) == 0:
        print("[segment_sam3] nothing to do.")
        return 0

    # --- Model ---
    print("[segment_sam3] building SAM 3 image model ...")
    ckpt = str(args.checkpoint) if args.checkpoint else None
    model = build_sam3_image_model(
        device=args.device,
        eval_mode=True,
        checkpoint_path=ckpt,
        load_from_HF=ckpt is None,
    )
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[args.dtype]
    autocast = torch.autocast("cuda", dtype=dtype) if args.device.startswith("cuda") else torch.cuda.amp.autocast(enabled=False)
    autocast.__enter__()
    # Keep a reference to the inference_mode context: calling __enter__() on a
    # temporary (torch.inference_mode().__enter__()) is garbage-collected
    # immediately and silently leaves grad enabled, which makes SAM3's fused ops
    # raise "Expected grad to be disabled".
    inference_mode = torch.inference_mode()
    inference_mode.__enter__()

    transform = build_transform(args.resolution)
    postprocessor = PostProcessImage(
        max_dets_per_img=-1,
        iou_type="segm",
        use_original_sizes_box=True,
        use_original_sizes_mask=True,
        convert_mask_to_rle=False,
        detection_threshold=args.confidence_threshold,
        to_cpu=True,
    )

    # --- Manifest ---
    man_f, writer = open_manifest(args.out_dir)

    # --- Batch loop ---
    qid_counter = 1
    rows_buf: list[dict] = []
    n_done = 0
    n_det = 0
    t0 = time.time()

    def flush():
        for r in rows_buf:
            writer.writerow(r)
        man_f.flush()
        rows_buf.clear()

    with tqdm(total=len(df), unit="img") as bar:
        for start in range(0, len(df), args.batch_size):
            batch_df = df.iloc[start:start + args.batch_size]
            datapoints = []
            row_meta = []  # parallel list: (obs dict, prompt, query_id)
            for _, obs in batch_df.iterrows():
                img_path = resolve_image_path(obs["image_path"])
                prompt = str(obs[args.prompt_field])
                qid = qid_counter
                qid_counter += 1
                try:
                    pil = Image.open(img_path).convert("RGB")
                except Exception as e:
                    rows_buf.append(row_from(obs, None, prompt, False, None, None, None, error=f"open:{e}"))
                    continue
                try:
                    dp = make_datapoint(pil, prompt, qid)
                    dp = transform(dp)
                    datapoints.append(dp)
                    row_meta.append((obs, prompt, qid))
                except Exception as e:
                    rows_buf.append(row_from(obs, None, prompt, False, None, None, None, error=f"transform:{e}"))
                    continue

            if not datapoints:
                n_done += len(batch_df)
                bar.update(len(batch_df))
                continue

            try:
                batch = collate(datapoints, dict_key="dummy")["dummy"]
                batch = copy_data_to_device(batch, torch.device(args.device), non_blocking=True)
                output = model(batch)
                results = postprocessor.process_results(output, batch.find_metadatas)
            except Exception as e:
                # whole-batch failure: record error for each, keep going
                for (obs, prompt, qid) in row_meta:
                    rows_buf.append(row_from(obs, None, prompt, False, None, None, None, error=f"forward:{e}"))
                n_done += len(batch_df)
                bar.update(len(batch_df))
                if len(rows_buf) >= args.flush_every * args.batch_size:
                    flush()
                continue

            results = results or {}
            for (obs, prompt, qid) in row_meta:
                res = results.get(qid)
                picked = best_mask_from_result(res) if res is not None else None
                if picked is None:
                    rows_buf.append(row_from(obs, None, prompt, False, None, None, None))
                    continue
                mask_bool, score, bbox = picked
                # fallback prompt if weak detection
                if score < args.confidence_threshold and args.fallback_field != "none":
                    fb_prompt = str(obs[args.fallback_field])
                    if fb_prompt and fb_prompt != prompt:
                        # single-image retry
                        try:
                            pil = Image.open(resolve_image_path(obs["image_path"])).convert("RGB")
                            dp2 = make_datapoint(pil, fb_prompt, qid_counter)
                            qid_counter += 1
                            dp2 = transform(dp2)
                            b2 = collate([dp2], dict_key="dummy")["dummy"]
                            b2 = copy_data_to_device(b2, torch.device(args.device), non_blocking=True)
                            out2 = model(b2)
                            res2 = postprocessor.process_results(out2, b2.find_metadatas) or {}
                            picked2 = best_mask_from_result(res2.get(qid_counter - 1))
                            if picked2 is not None:
                                mask_bool, score, bbox = picked2
                                prompt = fb_prompt
                        except Exception:
                            pass
                if score < args.confidence_threshold:
                    rows_buf.append(row_from(obs, None, prompt, False, score, bbox, None))
                    continue
                h, w = mask_bool.shape
                area_frac = float(mask_bool.sum()) / (h * w)
                mask_path = save_mask(mask_bool, obs["taxon"], obs["observation_id"], args.out_dir)
                rows_buf.append(row_from(obs, mask_path, prompt, True, score, bbox, area_frac))
                n_det += 1

            n_done += len(batch_df)
            bar.update(len(batch_df))
            bar.set_postfix(det=f"{n_det}/{n_done}", rate=f"{n_done/(time.time()-t0):.1f}img/s")
            if (start // args.batch_size) % args.flush_every == 0:
                flush()

    flush()
    man_f.close()
    dt = time.time() - t0
    print(f"[segment_sam3] done: {n_done} processed, {n_det} with detection "
          f"({100*n_det/max(n_done,1):.1f}%), {dt/60:.1f} min, {n_done/max(dt,1):.1f} img/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
