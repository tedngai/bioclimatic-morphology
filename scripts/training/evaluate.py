"""Evaluate a saved DINOv2 climate checkpoint on the train or validation split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from climate_dataset import (
    SPLIT_STRATEGIES,
    ClimateImageDataset,
    TargetStats,
    build_image_transform,
    load_training_dataframe,
    sample_dataframe,
    split_dataframe,
)
from train_dinov2 import (
    ClimateRegressor,
    build_per_taxon_limits,
    build_backbone,
    build_dataloader,
    evaluate,
    save_json,
    select_device,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--split", choices=["train", "val"], default="val")
    parser.add_argument("--csv-path", type=Path)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--image-size", type=int)
    parser.add_argument("--max-samples", type=int)
    parser.add_argument("--max-mammals", type=int)
    parser.add_argument("--max-birds", type=int)
    parser.add_argument("--split-strategy", choices=SPLIT_STRATEGIES)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu", "mps"], default="auto")
    parser.add_argument("--amp", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    checkpoint_args = checkpoint["args"]
    csv_path = args.csv_path or Path(checkpoint_args["csv_path"])
    image_size = args.image_size or int(checkpoint_args["image_size"])
    batch_size = args.batch_size or int(checkpoint_args["batch_size"])
    target_columns = list(checkpoint["target_columns"])
    target_stats = TargetStats.from_dict(checkpoint["target_stats"])
    split_strategy = args.split_strategy or checkpoint_args.get("split_strategy", "species")

    full_df = load_training_dataframe(csv_path, target_columns)
    train_df, val_df = split_dataframe(
        full_df,
        val_fraction=float(checkpoint_args["val_fraction"]),
        seed=int(checkpoint_args["seed"]),
        strategy=split_strategy,
    )
    split_df = train_df if args.split == "train" else val_df
    split_df = sample_dataframe(
        split_df,
        args.max_samples,
        seed=int(checkpoint_args["seed"]),
        per_taxon_limits=build_per_taxon_limits(args.max_mammals, args.max_birds),
    )

    dataset = ClimateImageDataset(
        split_df,
        target_columns,
        transform=build_image_transform(image_size, train=False),
        target_stats=target_stats,
    )
    loader = build_dataloader(dataset, batch_size=batch_size, num_workers=args.num_workers, shuffle=False)

    device = select_device(args.device)
    backbone, hidden_size = build_backbone(checkpoint_args["model_name"])
    model = ClimateRegressor(
        backbone=backbone,
        hidden_size=hidden_size,
        output_dim=len(target_columns),
        dropout=float(checkpoint_args["dropout"]),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    metrics = evaluate(
        model,
        loader,
        criterion=torch.nn.MSELoss(),
        device=device,
        target_columns=target_columns,
        target_stats=target_stats,
        amp_enabled=args.amp,
    )

    payload = {
        "checkpoint": str(args.checkpoint),
        "split": args.split,
        "rows": len(split_df),
        "metrics": metrics,
    }
    output_path = args.output_path or args.checkpoint.parent / f"eval_{args.split}.json"
    save_json(output_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
