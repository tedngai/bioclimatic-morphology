"""Train a DINOv2 encoder to predict climate features from animal photos."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from climate_dataset import (
    DEFAULT_CSV_PATH,
    DEFAULT_TARGET_COLUMNS,
    SPLIT_STRATEGIES,
    ClimateImageDataset,
    TargetStats,
    build_image_transform,
    load_training_dataframe,
    sample_dataframe,
    split_dataframe,
    summarize_split,
)

try:
    from transformers import AutoModel, get_cosine_schedule_with_warmup
except ImportError as exc:
    raise SystemExit(
        "Install `transformers` before training: python -m pip install transformers"
    ) from exc

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "models" / "dinov2_climate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-name", default="facebook/dinov2-base")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--prefetch-factor", type=int)
    parser.add_argument("--pin-memory", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--persistent-workers", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--split-strategy", choices=SPLIT_STRATEGIES, default="species")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--head-lr", type=float, default=1e-4)
    parser.add_argument("--backbone-lr", type=float, default=1e-6)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--unfreeze-last-n-blocks", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--warmup-ratio", type=float, default=0.05)
    parser.add_argument("--max-train-samples", type=int)
    parser.add_argument("--max-val-samples", type=int)
    parser.add_argument("--max-train-mammals", type=int)
    parser.add_argument("--max-train-birds", type=int)
    parser.add_argument("--max-val-mammals", type=int)
    parser.add_argument("--max-val-birds", type=int)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu", "mps"], default="auto")
    parser.add_argument("--amp", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--log-tensorboard", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tensorboard-dir", type=Path)
    parser.add_argument("--tensorboard-log-every-batches", type=int, default=100)
    parser.add_argument("--resume-checkpoint", type=Path)
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def select_device(requested: str) -> torch.device:
    if requested == "cuda":
        return torch.device("cuda")
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "mps":
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_per_taxon_limits(mammals: int | None, birds: int | None) -> dict[str, int | None]:
    limits = {"mammals": mammals, "birds": birds}
    if all(value is None for value in limits.values()):
        return {}
    return limits


class ClimateRegressor(nn.Module):
    """DINOv2 backbone plus a small regression head."""

    def __init__(self, backbone: nn.Module, hidden_size: int, output_dim: int, dropout: float = 0.1):
        super().__init__()
        self.backbone = backbone
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Linear(hidden_size, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, output_dim),
        )

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        outputs = self.backbone(pixel_values=pixel_values)
        pooled = getattr(outputs, "pooler_output", None)
        if pooled is None:
            pooled = outputs.last_hidden_state[:, 0]
        return self.head(pooled)


def build_backbone(model_name: str) -> tuple[nn.Module, int]:
    backbone = AutoModel.from_pretrained(model_name)
    hidden_size = int(backbone.config.hidden_size)
    return backbone, hidden_size


def freeze_backbone(backbone: nn.Module, unfreeze_last_n_blocks: int) -> None:
    for param in backbone.parameters():
        param.requires_grad = False

    if unfreeze_last_n_blocks <= 0:
        return

    blocks = getattr(getattr(backbone, "encoder", None), "layer", None)
    if blocks is None:
        raise ValueError("Unsupported backbone: expected encoder.layer blocks")

    for block in list(blocks)[-unfreeze_last_n_blocks:]:
        for param in block.parameters():
            param.requires_grad = True

    for attr in ("layernorm", "post_layernorm"):
        module = getattr(backbone, attr, None)
        if module is not None:
            for param in module.parameters():
                param.requires_grad = True


def build_dataloader(
    dataset: ClimateImageDataset,
    batch_size: int,
    num_workers: int,
    shuffle: bool,
    pin_memory: bool | None = None,
    persistent_workers: bool | None = None,
    prefetch_factor: int | None = None,
) -> DataLoader:
    if pin_memory is None:
        pin_memory = torch.cuda.is_available()

    loader_kwargs = {
        "dataset": dataset,
        "batch_size": batch_size,
        "shuffle": shuffle,
        "num_workers": num_workers,
        "pin_memory": pin_memory,
    }

    if num_workers > 0:
        if persistent_workers is None:
            persistent_workers = True
        loader_kwargs["persistent_workers"] = persistent_workers
        if prefetch_factor is not None:
            loader_kwargs["prefetch_factor"] = prefetch_factor

    return DataLoader(
        **loader_kwargs,
    )


def _safe_pearsonr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2:
        return float("nan")
    if np.allclose(y_true.std(), 0) or np.allclose(y_pred.std(), 0):
        return float("nan")
    return float(np.corrcoef(y_true, y_pred)[0, 1])


def compute_regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_columns: list[str],
) -> dict:
    per_target: dict[str, dict[str, float]] = {}
    r2_values = []
    mae_values = []

    for idx, column in enumerate(target_columns):
        truth = y_true[:, idx]
        pred = y_pred[:, idx]
        mse = float(np.mean((pred - truth) ** 2))
        mae = float(np.mean(np.abs(pred - truth)))
        ss_res = float(np.sum((truth - pred) ** 2))
        ss_tot = float(np.sum((truth - truth.mean()) ** 2))
        r2 = float("nan") if math.isclose(ss_tot, 0.0) else 1.0 - (ss_res / ss_tot)
        corr = _safe_pearsonr(truth, pred)

        per_target[column] = {
            "mse": mse,
            "mae": mae,
            "r2": r2,
            "pearson_r": corr,
        }
        r2_values.append(r2)
        mae_values.append(mae)

    return {
        "mean_r2": float(np.nanmean(r2_values)),
        "mean_mae": float(np.nanmean(mae_values)),
        "per_target": per_target,
    }


def flatten_metrics(prefix: str, metrics: dict) -> dict[str, float]:
    flat = {
        f"{prefix}_mean_r2": metrics["mean_r2"],
        f"{prefix}_mean_mae": metrics["mean_mae"],
    }
    for column, values in metrics["per_target"].items():
        for key, value in values.items():
            flat[f"{prefix}_{column}_{key}"] = value
    return flat


def create_summary_writer(args: argparse.Namespace):
    if not args.log_tensorboard:
        return None

    try:
        from torch.utils.tensorboard import SummaryWriter
    except ImportError as exc:
        raise SystemExit(
            "Install `tensorboard` before enabling TensorBoard logging: python -m pip install tensorboard"
        ) from exc

    log_dir = args.tensorboard_dir or (args.output_dir / "tensorboard")
    return SummaryWriter(log_dir=str(log_dir))


def log_tensorboard_train_step(
    writer,
    global_batch_step: int,
    train_loss: float,
    optimizer,
) -> None:
    if writer is None:
        return

    writer.add_scalar("loss/train_step", train_loss, global_batch_step)
    writer.add_scalar("lr/head_step", optimizer.param_groups[0]["lr"], global_batch_step)
    if len(optimizer.param_groups) > 1:
        writer.add_scalar("lr/backbone_step", optimizer.param_groups[1]["lr"], global_batch_step)


def log_tensorboard_epoch_metrics(writer, epoch: int, train_loss: float, val_metrics: dict, optimizer) -> None:
    if writer is None:
        return

    writer.add_scalar("loss/train", train_loss, epoch)
    writer.add_scalar("loss/val", val_metrics["loss"], epoch)
    writer.add_scalar("metrics/val_mean_r2", val_metrics["mean_r2"], epoch)
    writer.add_scalar("metrics/val_mean_mae", val_metrics["mean_mae"], epoch)
    writer.add_scalar("lr/head", optimizer.param_groups[0]["lr"], epoch)
    if len(optimizer.param_groups) > 1:
        writer.add_scalar("lr/backbone", optimizer.param_groups[1]["lr"], epoch)

    for column, values in val_metrics["per_target"].items():
        for metric_name, metric_value in values.items():
            writer.add_scalar(f"val/{column}/{metric_name}", metric_value, epoch)


def load_resume_state(
    resume_checkpoint: Path | None,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler,
) -> tuple[int, float, list[dict]]:
    if resume_checkpoint is None:
        return 1, float("-inf"), []

    checkpoint = torch.load(resume_checkpoint, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    scheduler_state = checkpoint.get("scheduler_state_dict")
    if scheduler_state is not None:
        scheduler.load_state_dict(scheduler_state)

    start_epoch = int(checkpoint["epoch"]) + 1
    best_score = float(checkpoint.get("best_score", checkpoint["metrics"]["val"]["mean_r2"]))
    history_rows = list(checkpoint.get("history_rows", []))
    return start_epoch, best_score, history_rows


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    target_columns: list[str],
    target_stats: TargetStats,
    amp_enabled: bool,
) -> dict:
    model.eval()
    running_loss = 0.0
    total_items = 0
    predictions = []
    labels = []
    mean = torch.tensor(target_stats.mean, dtype=torch.float32)
    std = torch.tensor(target_stats.std, dtype=torch.float32)

    for batch in loader:
        pixel_values = batch["pixel_values"].to(device, non_blocking=True)
        batch_labels = batch["labels"].to(device, non_blocking=True)

        use_amp = amp_enabled and device.type == "cuda"
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
            outputs = model(pixel_values)
            loss = criterion(outputs, batch_labels)

        batch_size = pixel_values.size(0)
        running_loss += loss.item() * batch_size
        total_items += batch_size
        predictions.append(outputs.detach().cpu())
        labels.append(batch_labels.detach().cpu())

    y_pred = torch.cat(predictions)
    y_true = torch.cat(labels)
    y_pred = (y_pred * std) + mean
    y_true = (y_true * std) + mean
    metrics = compute_regression_metrics(y_true.numpy(), y_pred.numpy(), target_columns)
    metrics["loss"] = running_loss / max(total_items, 1)
    return metrics


def serialize_args(args: argparse.Namespace) -> dict:
    payload = {}
    for key, value in vars(args).items():
        if isinstance(value, Path):
            payload[key] = str(value)
        else:
            payload[key] = value
    return payload


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler,
    epoch: int,
    args: argparse.Namespace,
    target_columns: list[str],
    target_stats: TargetStats,
    metrics: dict,
    best_score: float,
    history_rows: list[dict],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler is not None else None,
            "args": serialize_args(args),
            "target_columns": target_columns,
            "target_stats": target_stats.to_dict(),
            "metrics": metrics,
            "best_score": best_score,
            "history_rows": history_rows,
        },
        path,
    )


def train(args: argparse.Namespace) -> None:
    seed_everything(args.seed)
    device = select_device(args.device)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    writer = create_summary_writer(args)

    target_columns = list(DEFAULT_TARGET_COLUMNS)
    full_df = load_training_dataframe(args.csv_path, target_columns)
    train_df, val_df = split_dataframe(
        full_df,
        val_fraction=args.val_fraction,
        seed=args.seed,
        strategy=args.split_strategy,
    )
    train_df = sample_dataframe(
        train_df,
        args.max_train_samples,
        args.seed,
        per_taxon_limits=build_per_taxon_limits(args.max_train_mammals, args.max_train_birds),
    )
    val_df = sample_dataframe(
        val_df,
        args.max_val_samples,
        args.seed,
        per_taxon_limits=build_per_taxon_limits(args.max_val_mammals, args.max_val_birds),
    )
    if args.resume_checkpoint is not None:
        resume_payload = torch.load(args.resume_checkpoint, map_location="cpu")
        target_stats = TargetStats.from_dict(resume_payload["target_stats"])
    else:
        target_stats = TargetStats.from_dataframe(train_df, target_columns)

    train_dataset = ClimateImageDataset(
        train_df,
        target_columns,
        transform=build_image_transform(args.image_size, train=True),
        target_stats=target_stats,
    )
    val_dataset = ClimateImageDataset(
        val_df,
        target_columns,
        transform=build_image_transform(args.image_size, train=False),
        target_stats=target_stats,
    )

    train_loader = build_dataloader(
        train_dataset,
        args.batch_size,
        args.num_workers,
        shuffle=True,
        pin_memory=args.pin_memory,
        persistent_workers=args.persistent_workers,
        prefetch_factor=args.prefetch_factor,
    )
    val_loader = build_dataloader(
        val_dataset,
        args.batch_size,
        args.num_workers,
        shuffle=False,
        pin_memory=args.pin_memory,
        persistent_workers=args.persistent_workers,
        prefetch_factor=args.prefetch_factor,
    )

    backbone, hidden_size = build_backbone(args.model_name)
    freeze_backbone(backbone, args.unfreeze_last_n_blocks)
    model = ClimateRegressor(
        backbone=backbone,
        hidden_size=hidden_size,
        output_dim=len(target_columns),
        dropout=args.dropout,
    ).to(device)

    head_params = [
        param
        for name, param in model.named_parameters()
        if param.requires_grad and not name.startswith("backbone.")
    ]
    backbone_params = [
        param
        for name, param in model.named_parameters()
        if param.requires_grad and name.startswith("backbone.")
    ]

    optimizer_groups = [{"params": head_params, "lr": args.head_lr}]
    if backbone_params:
        optimizer_groups.append({"params": backbone_params, "lr": args.backbone_lr})

    optimizer = AdamW(optimizer_groups, weight_decay=args.weight_decay)
    criterion = nn.MSELoss()
    updates_per_epoch = math.ceil(len(train_loader) / max(args.grad_accum_steps, 1))
    total_updates = max(args.epochs * updates_per_epoch, 1)
    warmup_updates = int(total_updates * args.warmup_ratio)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_updates,
        num_training_steps=total_updates,
    )
    scaler = torch.amp.GradScaler("cuda", enabled=args.amp and device.type == "cuda")
    start_epoch, best_score, history_rows = load_resume_state(
        args.resume_checkpoint,
        model,
        optimizer,
        scheduler,
    )

    metadata = {
        "model_name": args.model_name,
        "device": str(device),
        "target_columns": target_columns,
        "target_stats": target_stats.to_dict(),
        "train_split": summarize_split(train_df),
        "val_split": summarize_split(val_df),
        "args": serialize_args(args),
    }
    save_json(args.output_dir / "run_config.json", metadata)

    for epoch in range(start_epoch, args.epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        running_loss = 0.0
        total_items = 0
        interval_loss = 0.0
        interval_items = 0

        for step, batch in enumerate(train_loader, start=1):
            global_batch_step = ((epoch - 1) * len(train_loader)) + step
            pixel_values = batch["pixel_values"].to(device, non_blocking=True)
            labels = batch["labels"].to(device, non_blocking=True)
            use_amp = args.amp and device.type == "cuda"

            with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
                predictions = model(pixel_values)
                loss = criterion(predictions, labels)
                loss = loss / max(args.grad_accum_steps, 1)

            scaler.scale(loss).backward()

            should_step = step % max(args.grad_accum_steps, 1) == 0 or step == len(train_loader)
            if should_step:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
                scheduler.step()

            batch_size = pixel_values.size(0)
            batch_loss = loss.item() * max(args.grad_accum_steps, 1)
            running_loss += batch_loss * batch_size
            total_items += batch_size
            interval_loss += batch_loss * batch_size
            interval_items += batch_size

            should_log_train_step = (
                writer is not None
                and args.tensorboard_log_every_batches > 0
                and (step % args.tensorboard_log_every_batches == 0 or step == len(train_loader))
            )
            if should_log_train_step:
                log_tensorboard_train_step(
                    writer,
                    global_batch_step=global_batch_step,
                    train_loss=interval_loss / max(interval_items, 1),
                    optimizer=optimizer,
                )
                writer.flush()
                interval_loss = 0.0
                interval_items = 0

        train_loss = running_loss / max(total_items, 1)
        val_metrics = evaluate(
            model,
            val_loader,
            criterion,
            device,
            target_columns,
            target_stats,
            amp_enabled=args.amp,
        )
        score = val_metrics["mean_r2"]

        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "learning_rate_head": optimizer.param_groups[0]["lr"],
        }
        if len(optimizer.param_groups) > 1:
            row["learning_rate_backbone"] = optimizer.param_groups[1]["lr"]
        row.update(flatten_metrics("val", val_metrics))
        row["val_loss"] = val_metrics["loss"]
        history_rows.append(row)
        log_tensorboard_epoch_metrics(writer, epoch, train_loss, val_metrics, optimizer)

        with open(args.output_dir / "history.csv", "w", newline="") as handle:
            csv_writer = csv.DictWriter(handle, fieldnames=history_rows[0].keys())
            csv_writer.writeheader()
            csv_writer.writerows(history_rows)

        checkpoint_metrics = {"train_loss": train_loss, "val": val_metrics}
        improved = score > best_score
        next_best_score = max(best_score, score)
        save_checkpoint(
            args.output_dir / "last.pt",
            model,
            optimizer,
            scheduler,
            epoch,
            args,
            target_columns,
            target_stats,
            checkpoint_metrics,
            next_best_score,
            history_rows,
        )
        if improved:
            best_score = next_best_score
            save_checkpoint(
                args.output_dir / "best.pt",
                model,
                optimizer,
                scheduler,
                epoch,
                args,
                target_columns,
                target_stats,
                checkpoint_metrics,
                best_score,
                history_rows,
            )

        print(
            f"epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} | val_mean_r2={val_metrics['mean_r2']:.4f}"
        )

    if writer is not None:
        writer.flush()
        writer.close()


def main() -> int:
    args = parse_args()
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
