"""Dataset utilities for climate regression from animal photos."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
from torchvision.transforms import InterpolationMode

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"
DEFAULT_CSV_PATH = DATA_VISION / "train_all.csv"

DEFAULT_TARGET_COLUMNS = [
    "wbt_c",
    "vpd_kpa",
    "diurnal_range_c",
    "solar_wm2",
    "temperature_2m_mean",
]

DINO_MEAN = (0.485, 0.456, 0.406)
DINO_STD = (0.229, 0.224, 0.225)
SPLIT_STRATEGIES = ("species", "row")

IMAGE_MODES = ("full", "crop", "masked")
DEFAULT_SEGMENTATION_MANIFEST = DATA_VISION / "segmented" / "manifest.csv"
MASKED_BACKGROUND_VALUE = 128
MIN_CROP_PIXELS = 32.0


@dataclass(slots=True)
class TargetStats:
    """Per-target normalization stats derived from the training split."""

    columns: list[str]
    mean: np.ndarray
    std: np.ndarray

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, columns: list[str]) -> "TargetStats":
        mean = df[columns].mean().to_numpy(dtype=np.float32)
        std = df[columns].std(ddof=0).to_numpy(dtype=np.float32)
        std = np.where(std == 0, 1.0, std)
        return cls(columns=list(columns), mean=mean, std=std)

    @classmethod
    def from_dict(cls, payload: dict) -> "TargetStats":
        return cls(
            columns=list(payload["columns"]),
            mean=np.asarray(payload["mean"], dtype=np.float32),
            std=np.asarray(payload["std"], dtype=np.float32),
        )

    def to_dict(self) -> dict:
        return {
            "columns": self.columns,
            "mean": self.mean.tolist(),
            "std": self.std.tolist(),
        }

    def align(self, columns: list[str]) -> tuple[np.ndarray, np.ndarray]:
        index = {column: i for i, column in enumerate(self.columns)}
        mean = np.asarray([self.mean[index[column]] for column in columns], dtype=np.float32)
        std = np.asarray([self.std[index[column]] for column in columns], dtype=np.float32)
        return mean, std


def load_training_dataframe(
    csv_path: str | Path = DEFAULT_CSV_PATH,
    target_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Load the paired image-climate dataset with only required columns."""

    target_columns = target_columns or DEFAULT_TARGET_COLUMNS
    csv_path = Path(csv_path)
    usecols = ["observation_id", "image_path", "species", "taxon", *target_columns]
    df = pd.read_csv(csv_path, usecols=usecols)
    df = df.dropna(subset=["image_path", "species", *target_columns]).copy()
    df[target_columns] = df[target_columns].astype(np.float32)
    return df.reset_index(drop=True)


def split_species_holdout(
    df: pd.DataFrame,
    val_fraction: float = 0.1,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by species so the same species never appears in both splits."""

    if not 0.0 <= val_fraction < 1.0:
        raise ValueError("val_fraction must be in [0, 1)")

    if val_fraction == 0:
        return df.reset_index(drop=True), df.iloc[0:0].copy()

    rng = np.random.default_rng(seed)
    val_species: set[str] = set()

    for _, taxon_df in df.groupby("taxon", sort=True):
        species = taxon_df["species"].dropna().unique().tolist()
        if len(species) < 2:
            continue
        rng.shuffle(species)
        n_val = int(round(len(species) * val_fraction))
        n_val = max(1, n_val)
        n_val = min(n_val, len(species) - 1)
        val_species.update(species[:n_val])

    val_mask = df["species"].isin(val_species)
    train_df = df.loc[~val_mask].copy().reset_index(drop=True)
    val_df = df.loc[val_mask].copy().reset_index(drop=True)

    if train_df.empty or val_df.empty:
        raise ValueError("species split produced an empty train or validation split")

    return train_df, val_df


def split_row_holdout(
    df: pd.DataFrame,
    val_fraction: float = 0.1,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Simple random row split for smoke tests and ablations."""

    if not 0.0 <= val_fraction < 1.0:
        raise ValueError("val_fraction must be in [0, 1)")

    if val_fraction == 0:
        return df.reset_index(drop=True), df.iloc[0:0].copy()

    val_df = df.sample(frac=val_fraction, random_state=seed)
    train_df = df.drop(index=val_df.index)
    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    if train_df.empty or val_df.empty:
        raise ValueError("row split produced an empty train or validation split")

    return train_df, val_df


def split_dataframe(
    df: pd.DataFrame,
    val_fraction: float = 0.1,
    seed: int = 42,
    strategy: str = "species",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the dataset with a configurable strategy."""

    if strategy == "species":
        return split_species_holdout(df, val_fraction=val_fraction, seed=seed)
    if strategy == "row":
        return split_row_holdout(df, val_fraction=val_fraction, seed=seed)
    raise ValueError(f"Unknown split strategy: {strategy}")


def sample_dataframe(
    df: pd.DataFrame,
    max_samples: int | None,
    seed: int,
    per_taxon_limits: Mapping[str, int | None] | None = None,
) -> pd.DataFrame:
    """Optionally subsample rows globally and/or per taxon."""

    sampled = df
    if per_taxon_limits:
        sampled_parts = []
        for offset, (taxon, taxon_df) in enumerate(df.groupby("taxon", sort=True)):
            limit = per_taxon_limits.get(taxon)
            if limit is None or limit >= len(taxon_df):
                sampled_parts.append(taxon_df)
            else:
                sampled_parts.append(taxon_df.sample(n=limit, random_state=seed + offset))
        sampled = pd.concat(sampled_parts, axis=0)
        sampled = sampled.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    if max_samples is None or len(sampled) <= max_samples:
        return sampled.reset_index(drop=True)
    return sampled.sample(n=max_samples, random_state=seed).reset_index(drop=True)


def build_image_transform(image_size: int = 224, train: bool = False) -> transforms.Compose:
    """Build DINOv2-compatible image preprocessing."""

    if train:
        ops = [
            transforms.RandomResizedCrop(
                image_size,
                scale=(0.8, 1.0),
                interpolation=InterpolationMode.BICUBIC,
            ),
            transforms.RandomHorizontalFlip(),
        ]
    else:
        resize_size = int(round(image_size * 256 / 224))
        ops = [
            transforms.Resize(resize_size, interpolation=InterpolationMode.BICUBIC),
            transforms.CenterCrop(image_size),
        ]

    ops.extend(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=DINO_MEAN, std=DINO_STD),
        ]
    )
    return transforms.Compose(ops)


@dataclass(slots=True)
class SegmentationRecord:
    """Per-observation SAM 3 output used by the crop/masked image modes."""

    mask_path: Path | None
    bbox: tuple[float, float, float, float] | None
    has_detection: bool


def load_segmentation_index(
    manifest_path: str | Path,
    observation_ids: set[int] | None = None,
) -> dict[int, SegmentationRecord]:
    """Load a SAM 3 manifest into an ``observation_id -> record`` index.

    Rows without a detection are kept (``has_detection=False``) so callers can
    fall back to the full frame. When ``observation_ids`` is given, only those
    rows are read to keep memory bounded.
    """

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Segmentation manifest not found: {manifest_path}. "
            "Run scripts/segmentation/segment_sam3.py first."
        )

    columns = [
        "observation_id",
        "mask_path",
        "has_detection",
        "bbox_x0",
        "bbox_y0",
        "bbox_x1",
        "bbox_y1",
    ]
    manifest = pd.read_csv(manifest_path, usecols=columns)
    if observation_ids is not None:
        manifest = manifest[manifest["observation_id"].isin(observation_ids)]

    index: dict[int, SegmentationRecord] = {}
    for row in manifest.itertuples(index=False):
        bbox = None
        if bool(row.has_detection) and pd.notna(row.bbox_x0) and pd.notna(row.bbox_x1):
            bbox = (float(row.bbox_x0), float(row.bbox_y0), float(row.bbox_x1), float(row.bbox_y1))
        mask_path = None
        if isinstance(row.mask_path, str) and row.mask_path:
            mask_path = Path(row.mask_path)
            if not mask_path.is_absolute():
                mask_path = PROJECT_ROOT / mask_path
        index[int(row.observation_id)] = SegmentationRecord(
            mask_path=mask_path,
            bbox=bbox,
            has_detection=bool(row.has_detection),
        )
    return index


def _crop_with_bbox(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
    pad_fraction: float = 0.10,
    min_pixels: float = MIN_CROP_PIXELS,
) -> Image.Image:
    """Crop to ``bbox`` (xyxy) with padding, enforcing a minimum side length."""

    width, height = image.size
    x0, y0, x1, y1 = bbox
    pad = pad_fraction * max(x1 - x0, y1 - y0, 1.0)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad

    if x1 - x0 < min_pixels:
        center = (x0 + x1) / 2
        x0, x1 = center - min_pixels / 2, center + min_pixels / 2
    if y1 - y0 < min_pixels:
        center = (y0 + y1) / 2
        y0, y1 = center - min_pixels / 2, center + min_pixels / 2

    x0 = max(0, int(round(x0)))
    y0 = max(0, int(round(y0)))
    x1 = min(width, int(round(x1)))
    y1 = min(height, int(round(y1)))
    if x1 <= x0 or y1 <= y0:
        return image
    return image.crop((x0, y0, x1, y1))


def _apply_background_mask(
    image: Image.Image,
    mask_path: Path,
    background: int = MASKED_BACKGROUND_VALUE,
) -> Image.Image:
    """Return the image with all non-animal pixels set to a neutral gray."""

    with Image.open(mask_path) as mask_image:
        mask = mask_image.convert("L")
        if mask.size != image.size:
            mask = mask.resize(image.size, resample=Image.Resampling.NEAREST)
        mask_array = np.asarray(mask) > 127

    array = np.asarray(image).copy()
    array[~mask_array] = background
    return Image.fromarray(array)


class ClimateImageDataset(Dataset):
    """Image dataset for climate regression targets.

    ``image_mode`` selects how the animal is presented to the model:

    - ``full``: the original photograph (baseline).
    - ``crop``: bounding-box crop around the detected animal (from the SAM 3 manifest).
    - ``masked``: non-animal pixels replaced by a neutral gray using the SAM 3 mask.

    For ``crop``/``masked``, observations without a SAM 3 detection (or a missing
    mask file) fall back to the full frame; ``detection_coverage`` reports the
    fraction of rows that have a usable detection.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        target_columns: list[str],
        transform: transforms.Compose,
        image_root: str | Path = DATA_VISION,
        target_stats: TargetStats | None = None,
        max_open_attempts: int = 4,
        image_mode: str = "full",
        segmentation_manifest: str | Path | None = None,
        crop_pad_fraction: float = 0.10,
    ):
        if image_mode not in IMAGE_MODES:
            raise ValueError(f"Unknown image_mode '{image_mode}'; expected one of {IMAGE_MODES}")
        self.df = df.reset_index(drop=True)
        self.target_columns = list(target_columns)
        self.transform = transform
        self.image_root = Path(image_root)
        self.max_open_attempts = max_open_attempts
        self.image_mode = image_mode
        self.crop_pad_fraction = crop_pad_fraction

        self.segmentation_index: dict[int, SegmentationRecord] | None = None
        self.detection_coverage = 1.0
        if image_mode != "full":
            manifest_path = Path(segmentation_manifest) if segmentation_manifest else DEFAULT_SEGMENTATION_MANIFEST
            observation_ids = set(self.df["observation_id"].astype(int))
            self.segmentation_index = load_segmentation_index(manifest_path, observation_ids=observation_ids)
            detected = sum(
                1
                for obs_id in observation_ids
                if (record := self.segmentation_index.get(obs_id)) is not None and record.has_detection
            )
            self.detection_coverage = detected / max(len(observation_ids), 1)

        targets = self.df[self.target_columns].to_numpy(dtype=np.float32)
        if target_stats is not None:
            mean, std = target_stats.align(self.target_columns)
            targets = (targets - mean) / std
        self.targets = torch.from_numpy(targets)

    def __len__(self) -> int:
        return len(self.df)

    def _resolve_image_path(self, image_path: str) -> Path:
        path = Path(image_path)
        if path.is_absolute():
            return path
        return self.image_root / path

    def _load_image(self, row_index: int) -> tuple[Image.Image, int]:
        dataset_size = len(self.df)
        last_error: Exception | None = None

        # Skip the occasional missing/corrupt file without killing a long run.
        for offset in range(self.max_open_attempts):
            actual_index = (row_index + offset) % dataset_size
            row = self.df.iloc[actual_index]
            image_path = self._resolve_image_path(row["image_path"])
            try:
                with Image.open(image_path) as image:
                    loaded = image.convert("RGB")
                return loaded, actual_index
            except (FileNotFoundError, OSError) as exc:
                last_error = exc

        raise RuntimeError(f"Unable to load image near index {row_index}") from last_error

    def _apply_variant(self, image: Image.Image, row_index: int) -> tuple[Image.Image, str]:
        """Apply the configured crop/mask variant; fall back to the full frame."""

        if self.image_mode == "full" or self.segmentation_index is None:
            return image, "full"

        obs_id = int(self.df.iloc[row_index]["observation_id"])
        record = self.segmentation_index.get(obs_id)
        if record is None or not record.has_detection:
            return image, "full"

        if self.image_mode == "crop" and record.bbox is not None:
            return _crop_with_bbox(image, record.bbox, pad_fraction=self.crop_pad_fraction), "crop"
        if self.image_mode == "masked" and record.mask_path is not None and record.mask_path.exists():
            return _apply_background_mask(image, record.mask_path), "masked"
        return image, "full"

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str | int]:
        image, actual_index = self._load_image(index)
        image, variant = self._apply_variant(image, actual_index)
        pixel_values = self.transform(image)
        row = self.df.iloc[actual_index]
        return {
            "pixel_values": pixel_values,
            "labels": self.targets[actual_index],
            "observation_id": int(row["observation_id"]),
            "species": str(row["species"]),
            "taxon": str(row["taxon"]),
            "image_path": str(row["image_path"]),
            "image_variant": variant,
        }


def summarize_split(df: pd.DataFrame) -> dict[str, int]:
    """Small split summary for logs and metadata."""

    return {
        "rows": int(len(df)),
        "species": int(df["species"].nunique()),
        "mammals": int((df["taxon"] == "mammals").sum()),
        "birds": int((df["taxon"] == "birds").sum()),
    }
