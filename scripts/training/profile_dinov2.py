"""Profile the DINOv2 training pipeline to find dataloader vs GPU bottlenecks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch import nn

from climate_dataset import (
    DEFAULT_CSV_PATH,
    DEFAULT_TARGET_COLUMNS,
    ClimateImageDataset,
    TargetStats,
    build_image_transform,
    load_training_dataframe,
    sample_dataframe,
    split_dataframe,
    summarize_split,
)
from train_dinov2 import (
    ClimateRegressor,
    build_backbone,
    build_dataloader,
    build_per_taxon_limits,
    freeze_backbone,
    seed_everything,
    select_device,
)

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "outputs" / "profiles" / "dinov2_pipeline_profile.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--mode", choices=["loader", "train", "all"], default="all")
    parser.add_argument("--model-name", default="facebook/dinov2-base")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--prefetch-factor", type=int)
    parser.add_argument("--pin-memory", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--persistent-workers", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--split-strategy", choices=["species", "row"], default="species")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--head-lr", type=float, default=1e-4)
    parser.add_argument("--backbone-lr", type=float, default=1e-6)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--unfreeze-last-n-blocks", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--max-train-samples", type=int, default=4096)
    parser.add_argument("--max-train-mammals", type=int)
    parser.add_argument("--max-train-birds", type=int)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu", "mps"], default="auto")
    parser.add_argument("--amp", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--profile-steps", type=int, default=40)
    return parser.parse_args()


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def next_batch(iterator, loader):
    try:
        return next(iterator), iterator
    except StopIteration:
        iterator = iter(loader)
        return next(iterator), iterator


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def summarize_records(records: list[dict], time_keys: list[str]) -> dict:
    summary = {
        "steps": len(records),
        "items": int(sum(record["items"] for record in records)),
        "batch_size_mean": float(np.mean([record["items"] for record in records])),
    }
    for key in time_keys:
        values = np.asarray([record[key] for record in records], dtype=np.float64)
        summary[f"{key}_mean_ms"] = float(values.mean() * 1000.0)
        summary[f"{key}_p50_ms"] = float(np.percentile(values, 50) * 1000.0)
        summary[f"{key}_p95_ms"] = float(np.percentile(values, 95) * 1000.0)
        summary[f"{key}_total_s"] = float(values.sum())
    return summary


def build_train_loader(args: argparse.Namespace):
    target_columns = list(DEFAULT_TARGET_COLUMNS)
    full_df = load_training_dataframe(args.csv_path, target_columns)
    train_df, _ = split_dataframe(
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
    target_stats = TargetStats.from_dataframe(train_df, target_columns)
    dataset = ClimateImageDataset(
        train_df,
        target_columns,
        transform=build_image_transform(args.image_size, train=True),
        target_stats=target_stats,
    )
    loader = build_dataloader(
        dataset,
        args.batch_size,
        args.num_workers,
        shuffle=True,
        pin_memory=args.pin_memory,
        persistent_workers=args.persistent_workers,
        prefetch_factor=args.prefetch_factor,
    )
    return loader, target_columns, target_stats, summarize_split(train_df)


def benchmark_loader(loader, warmup_steps: int, profile_steps: int) -> dict:
    iterator = iter(loader)
    records = []
    total_steps = warmup_steps + profile_steps
    last_batch_end = perf_counter()

    for step in range(total_steps):
        batch, iterator = next_batch(iterator, loader)
        batch_ready = perf_counter()
        items = int(batch["pixel_values"].size(0))
        if step >= warmup_steps:
            records.append(
                {
                    "items": items,
                    "data_wait_s": batch_ready - last_batch_end,
                }
            )
        last_batch_end = perf_counter()

    summary = summarize_records(records, ["data_wait_s"])
    total_wait = summary["data_wait_s_total_s"]
    summary["images_per_sec"] = float(summary["items"] / total_wait) if total_wait > 0 else float("inf")
    return summary


def build_model_and_optimizer(args: argparse.Namespace, output_dim: int, device: torch.device):
    backbone, hidden_size = build_backbone(args.model_name)
    freeze_backbone(backbone, args.unfreeze_last_n_blocks)
    model = ClimateRegressor(
        backbone=backbone,
        hidden_size=hidden_size,
        output_dim=output_dim,
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
    optimizer = torch.optim.AdamW(optimizer_groups, weight_decay=args.weight_decay)
    return model, optimizer


def benchmark_train_step(
    loader,
    args: argparse.Namespace,
    device: torch.device,
    output_dim: int,
) -> dict:
    model, optimizer = build_model_and_optimizer(args, output_dim=output_dim, device=device)
    criterion = nn.MSELoss()
    scaler = torch.amp.GradScaler("cuda", enabled=args.amp and device.type == "cuda")
    iterator = iter(loader)
    records = []
    total_steps = args.warmup_steps + args.profile_steps
    last_step_end = perf_counter()

    model.train()
    optimizer.zero_grad(set_to_none=True)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    for step in range(total_steps):
        batch, iterator = next_batch(iterator, loader)
        batch_ready = perf_counter()
        data_wait_s = batch_ready - last_step_end

        synchronize(device)
        transfer_start = perf_counter()
        pixel_values = batch["pixel_values"].to(device, non_blocking=True)
        labels = batch["labels"].to(device, non_blocking=True)
        synchronize(device)
        h2d_s = perf_counter() - transfer_start

        use_amp = args.amp and device.type == "cuda"
        forward_start = perf_counter()
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=use_amp):
            predictions = model(pixel_values)
            loss = criterion(predictions, labels)
            loss = loss / max(args.grad_accum_steps, 1)
        synchronize(device)
        forward_s = perf_counter() - forward_start

        backward_start = perf_counter()
        scaler.scale(loss).backward()
        synchronize(device)
        backward_s = perf_counter() - backward_start

        optimizer_start = perf_counter()
        should_step = (step + 1) % max(args.grad_accum_steps, 1) == 0
        if should_step:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
        synchronize(device)
        optimizer_s = perf_counter() - optimizer_start

        step_end = perf_counter()
        if step >= args.warmup_steps:
            items = int(pixel_values.size(0))
            compute_s = h2d_s + forward_s + backward_s + optimizer_s
            records.append(
                {
                    "items": items,
                    "data_wait_s": data_wait_s,
                    "h2d_s": h2d_s,
                    "forward_s": forward_s,
                    "backward_s": backward_s,
                    "optimizer_s": optimizer_s,
                    "compute_s": compute_s,
                    "cycle_s": data_wait_s + compute_s,
                    "loss": float(loss.detach().item() * max(args.grad_accum_steps, 1)),
                }
            )
        last_step_end = step_end

    summary = summarize_records(
        records,
        ["data_wait_s", "h2d_s", "forward_s", "backward_s", "optimizer_s", "compute_s", "cycle_s"],
    )
    total_cycle = summary["cycle_s_total_s"]
    total_compute = summary["compute_s_total_s"]
    total_wait = summary["data_wait_s_total_s"]
    summary["loss_mean"] = float(np.mean([record["loss"] for record in records]))
    summary["images_per_sec_end_to_end"] = float(summary["items"] / total_cycle) if total_cycle > 0 else float("inf")
    summary["images_per_sec_compute_only"] = float(summary["items"] / total_compute) if total_compute > 0 else float("inf")
    summary["dataloader_share_pct"] = float((total_wait / total_cycle) * 100.0) if total_cycle > 0 else 0.0
    summary["gpu_active_share_pct"] = float((total_compute / total_cycle) * 100.0) if total_cycle > 0 else 0.0
    if device.type == "cuda":
        summary["peak_cuda_memory_gib"] = float(torch.cuda.max_memory_allocated(device) / (1024 ** 3))
    del criterion
    del optimizer
    del model
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return summary


def print_loader_summary(summary: dict) -> None:
    print(
        "loader profile | "
        f"steps={summary['steps']} | images/sec={summary['images_per_sec']:.1f} | "
        f"wait_mean={summary['data_wait_s_mean_ms']:.1f} ms | "
        f"wait_p95={summary['data_wait_s_p95_ms']:.1f} ms"
    )


def print_train_summary(summary: dict) -> None:
    print(
        "train profile | "
        f"steps={summary['steps']} | end_to_end_img/s={summary['images_per_sec_end_to_end']:.1f} | "
        f"gpu_only_img/s={summary['images_per_sec_compute_only']:.1f} | "
        f"wait={summary['data_wait_s_mean_ms']:.1f} ms | "
        f"h2d={summary['h2d_s_mean_ms']:.1f} ms | "
        f"fwd={summary['forward_s_mean_ms']:.1f} ms | "
        f"bwd={summary['backward_s_mean_ms']:.1f} ms | "
        f"opt={summary['optimizer_s_mean_ms']:.1f} ms | "
        f"gpu_active={summary['gpu_active_share_pct']:.1f}% | "
        f"loader_wait={summary['dataloader_share_pct']:.1f}%"
    )
    peak_memory = summary.get("peak_cuda_memory_gib")
    if peak_memory is not None:
        print(f"train profile memory | peak_cuda_allocated={peak_memory:.2f} GiB")


def main() -> int:
    args = parse_args()
    if args.profile_steps <= 0:
        raise SystemExit("--profile-steps must be > 0")

    seed_everything(args.seed)
    device = select_device(args.device)
    loader, target_columns, _, split_summary = build_train_loader(args)

    results = {
        "config": {
            "csv_path": str(args.csv_path),
            "mode": args.mode,
            "model_name": args.model_name,
            "batch_size": args.batch_size,
            "num_workers": args.num_workers,
            "prefetch_factor": args.prefetch_factor,
            "pin_memory": args.pin_memory,
            "persistent_workers": args.persistent_workers,
            "image_size": args.image_size,
            "device": str(device),
            "amp": args.amp,
            "warmup_steps": args.warmup_steps,
            "profile_steps": args.profile_steps,
            "grad_accum_steps": args.grad_accum_steps,
            "unfreeze_last_n_blocks": args.unfreeze_last_n_blocks,
            "train_split": split_summary,
            "target_columns": target_columns,
        }
    }

    if args.mode in {"loader", "all"}:
        loader_summary = benchmark_loader(loader, args.warmup_steps, args.profile_steps)
        results["loader"] = loader_summary
        print_loader_summary(loader_summary)

    if args.mode in {"train", "all"}:
        train_summary = benchmark_train_step(loader, args, device, output_dim=len(target_columns))
        results["train"] = train_summary
        print_train_summary(train_summary)

    save_json(args.output_path, results)
    print(f"saved profile to {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
