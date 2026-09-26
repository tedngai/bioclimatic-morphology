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


class ClimateImageDataset(Dataset):
    """Image dataset for climate regression targets."""

    def __init__(
        self,
        df: pd.DataFrame,
        target_columns: list[str],
        transform: transforms.Compose,
        image_root: str | Path = DATA_VISION,
        target_stats: TargetStats | None = None,
        max_open_attempts: int = 4,
    ):
        self.df = df.reset_index(drop=True)
        self.target_columns = list(target_columns)
        self.transform = transform
        self.image_root = Path(image_root)
        self.max_open_attempts = max_open_attempts

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

    def _load_image(self, row_index: int) -> tuple[torch.Tensor, int]:
        dataset_size = len(self.df)
        last_error: Exception | None = None

        # Skip the occasional missing/corrupt file without killing a long run.
        for offset in range(self.max_open_attempts):
            actual_index = (row_index + offset) % dataset_size
            row = self.df.iloc[actual_index]
            image_path = self._resolve_image_path(row["image_path"])
            try:
                with Image.open(image_path) as image:
                    image = image.convert("RGB")
                    return self.transform(image), actual_index
            except (FileNotFoundError, OSError) as exc:
                last_error = exc

        raise RuntimeError(f"Unable to load image near index {row_index}") from last_error

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str | int]:
        pixel_values, actual_index = self._load_image(index)
        row = self.df.iloc[actual_index]
        return {
            "pixel_values": pixel_values,
            "labels": self.targets[actual_index],
            "observation_id": int(row["observation_id"]),
            "species": str(row["species"]),
            "taxon": str(row["taxon"]),
            "image_path": str(row["image_path"]),
        }


def summarize_split(df: pd.DataFrame) -> dict[str, int]:
    """Small split summary for logs and metadata."""

    return {
        "rows": int(len(df)),
        "species": int(df["species"].nunique()),
        "mammals": int((df["taxon"] == "mammals").sum()),
        "birds": int((df["taxon"] == "birds").sum()),
    }
