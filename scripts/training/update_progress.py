"""Refresh PROGRESS.xml from profiler outputs and training runs."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PROGRESS_PATH = PROJECT_ROOT / "PROGRESS.xml"
DEFAULT_PROFILES_DIR = PROJECT_ROOT / "outputs" / "profiles"
DEFAULT_MODELS_DIR = PROJECT_ROOT / "outputs" / "models"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress-path", type=Path, default=DEFAULT_PROGRESS_PATH)
    parser.add_argument("--profiles-dir", type=Path, default=DEFAULT_PROFILES_DIR)
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR)
    parser.add_argument("--memory-baseline-gib", type=float, default=6.0)
    parser.add_argument("--max-runs", type=int, default=8)
    return parser.parse_args()


def safe_float(value) -> float | None:
    if value in (None, "", "nan"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def replace_element(parent: ET.Element, child: ET.Element) -> ET.Element:
    existing = parent.find(child.tag)
    if existing is not None:
        parent.remove(existing)
    parent.append(child)
    return child


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def classify_run(name: str) -> str:
    lowered = name.lower()
    if "smoke" in lowered:
        return "smoke"
    if "probe" in lowered:
        return "probe"
    if "real" in lowered:
        return "real"
    return "train"


def load_history(history_path: Path) -> list[dict]:
    if not history_path.exists():
        return []
    with history_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def load_checkpoint_metadata(path: Path) -> dict | None:
    if not path.exists():
        return None

    try:
        from torch._subclasses.fake_tensor import FakeTensorMode
    except ImportError:
        FakeTensorMode = None

    try:
        if FakeTensorMode is not None:
            with FakeTensorMode():
                payload = torch.load(path, map_location="cpu")
        else:
            payload = torch.load(path, map_location="cpu")
    except Exception:
        return None

    metrics = payload.get("metrics", {})
    val_metrics = metrics.get("val", {}) if isinstance(metrics, dict) else {}
    return {
        "epoch": payload.get("epoch"),
        "best_score": safe_float(payload.get("best_score")),
        "train_loss": safe_float(metrics.get("train_loss")) if isinstance(metrics, dict) else None,
        "val_loss": safe_float(val_metrics.get("loss")) if isinstance(val_metrics, dict) else None,
        "val_mean_r2": safe_float(val_metrics.get("mean_r2")) if isinstance(val_metrics, dict) else None,
    }


def discover_profiles(profiles_dir: Path) -> tuple[list[dict], list[dict]]:
    loader_profiles = []
    train_profiles = []

    for path in sorted(profiles_dir.glob("*.json")):
        payload = load_json(path)
        if not payload:
            continue
        config = payload.get("config", {})
        common = {
            "name": path.stem,
            "path": path,
            "batch_size": config.get("batch_size"),
            "num_workers": config.get("num_workers"),
            "model_name": config.get("model_name"),
            "mtime": path.stat().st_mtime,
        }

        loader = payload.get("loader")
        if isinstance(loader, dict):
            loader_profiles.append(
                {
                    **common,
                    "images_per_sec": safe_float(loader.get("images_per_sec")),
                    "mean_wait_ms": safe_float(loader.get("data_wait_s_mean_ms")),
                    "p95_wait_ms": safe_float(loader.get("data_wait_s_p95_ms")),
                }
            )

        train = payload.get("train")
        if isinstance(train, dict):
            train_profiles.append(
                {
                    **common,
                    "images_per_sec_end_to_end": safe_float(train.get("images_per_sec_end_to_end")),
                    "loader_wait_pct": safe_float(train.get("dataloader_share_pct")),
                    "gpu_active_pct": safe_float(train.get("gpu_active_share_pct")),
                    "peak_cuda_memory_gib": safe_float(train.get("peak_cuda_memory_gib")),
                }
            )

    return loader_profiles, train_profiles


def pick_recommended_profile(train_profiles: list[dict], memory_baseline_gib: float) -> dict | None:
    if not train_profiles:
        return None

    scored = [
        profile
        for profile in train_profiles
        if profile.get("images_per_sec_end_to_end") is not None
    ]
    if not scored:
        return None

    within_memory = [
        profile
        for profile in scored
        if profile.get("peak_cuda_memory_gib") is not None
        and profile["peak_cuda_memory_gib"] <= memory_baseline_gib
    ]
    pool = within_memory or scored
    return max(pool, key=lambda profile: profile["images_per_sec_end_to_end"])


def build_profiling_element(
    existing: ET.Element | None,
    loader_profiles: list[dict],
    train_profiles: list[dict],
    recommended_profile: dict | None,
) -> ET.Element:
    profiling = ET.Element("profiling")
    if existing is not None:
        storage_transition = existing.find("storageTransition")
        if storage_transition is not None:
            profiling.append(storage_transition)

    if loader_profiles:
        best_loader = max(loader_profiles, key=lambda profile: profile.get("images_per_sec") or 0.0)
        result = ET.SubElement(profiling, "result", name=best_loader["name"], status="best-loader")
        add_metric(result, "images_per_sec", best_loader.get("images_per_sec"))
        add_metric(result, "mean_wait_ms", best_loader.get("mean_wait_ms"))
        add_metric(result, "p95_wait_ms", best_loader.get("p95_wait_ms"))

    best_train = None
    if train_profiles:
        best_train = max(train_profiles, key=lambda profile: profile.get("images_per_sec_end_to_end") or 0.0)

    if recommended_profile is not None:
        result = ET.SubElement(profiling, "result", name=recommended_profile["name"], status="recommended-baseline")
        add_metric(result, "images_per_sec_end_to_end", recommended_profile.get("images_per_sec_end_to_end"))
        add_metric(result, "loader_wait_pct", recommended_profile.get("loader_wait_pct"))
        add_metric(result, "gpu_active_pct", recommended_profile.get("gpu_active_pct"))
        add_metric(result, "peak_cuda_memory_gib", recommended_profile.get("peak_cuda_memory_gib"))

    if best_train is not None and best_train.get("name") != (recommended_profile or {}).get("name"):
        result = ET.SubElement(profiling, "result", name=best_train["name"], status="best-throughput")
        add_metric(result, "images_per_sec_end_to_end", best_train.get("images_per_sec_end_to_end"))
        add_metric(result, "loader_wait_pct", best_train.get("loader_wait_pct"))
        add_metric(result, "gpu_active_pct", best_train.get("gpu_active_pct"))
        add_metric(result, "peak_cuda_memory_gib", best_train.get("peak_cuda_memory_gib"))

    if recommended_profile is not None:
        loader_wait_pct = recommended_profile.get("loader_wait_pct") or 0.0
        conclusion_text = (
            "Current bottleneck is GPU compute rather than file I/O or dataloader starvation."
            if loader_wait_pct <= 5.0
            else "Current bottleneck still appears to be the dataloader or image I/O path."
        )
        ET.SubElement(profiling, "conclusion").text = conclusion_text

    return profiling


def add_metric(parent: ET.Element, name: str, value: float | None) -> None:
    if value is None:
        return
    ET.SubElement(parent, "metric", name=name, value=f"{value:.4f}".rstrip("0").rstrip("."))


def discover_runs(models_dir: Path) -> list[dict]:
    runs = []
    if not models_dir.exists():
        return runs

    for run_dir in sorted((path for path in models_dir.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True):
        run_config = load_json(run_dir / "run_config.json") or {}
        args = run_config.get("args", {}) if isinstance(run_config, dict) else {}
        history_rows = load_history(run_dir / "history.csv")
        best_ckpt = load_checkpoint_metadata(run_dir / "best.pt")
        last_ckpt = load_checkpoint_metadata(run_dir / "last.pt")

        last_history = history_rows[-1] if history_rows else {}
        val_r2_history = [safe_float(row.get("val_mean_r2")) for row in history_rows]
        val_r2_history = [value for value in val_r2_history if value is not None]
        completed_epochs = len(history_rows)
        last_epoch = safe_float(last_history.get("epoch"))
        if completed_epochs == 0 and last_ckpt and last_ckpt.get("epoch") is not None:
            completed_epochs = int(last_ckpt["epoch"])
        elif last_epoch is not None:
            completed_epochs = int(last_epoch)

        run = {
            "name": run_dir.name,
            "path": run_dir,
            "kind": classify_run(run_dir.name),
            "model_name": args.get("model_name") or run_config.get("model_name"),
            "batch_size": args.get("batch_size"),
            "num_workers": args.get("num_workers"),
            "epochs_configured": args.get("epochs"),
            "epochs_completed": completed_epochs,
            "best_val_mean_r2": (
                (best_ckpt or {}).get("val_mean_r2")
                if best_ckpt is not None and (best_ckpt or {}).get("val_mean_r2") is not None
                else (max(val_r2_history) if val_r2_history else None)
            ),
            "last_val_mean_r2": (
                (last_ckpt or {}).get("val_mean_r2")
                if last_ckpt is not None and (last_ckpt or {}).get("val_mean_r2") is not None
                else safe_float(last_history.get("val_mean_r2"))
            ),
            "last_val_loss": (
                (last_ckpt or {}).get("val_loss")
                if last_ckpt is not None and (last_ckpt or {}).get("val_loss") is not None
                else safe_float(last_history.get("val_loss"))
            ),
            "last_train_loss": (
                (last_ckpt or {}).get("train_loss")
                if last_ckpt is not None and (last_ckpt or {}).get("train_loss") is not None
                else safe_float(last_history.get("train_loss"))
            ),
            "mtime": run_dir.stat().st_mtime,
        }
        runs.append(run)

    return runs


def build_training_runs_element(runs: list[dict], max_runs: int) -> ET.Element:
    training_runs = ET.Element("trainingRuns")
    for run in runs[:max_runs]:
        status = "completed" if run.get("epochs_completed") else "created"
        run_element = ET.SubElement(
            training_runs,
            "run",
            name=run["name"],
            kind=run["kind"],
            status=status,
            path=str(run["path"].relative_to(PROJECT_ROOT)),
        )
        for key, attribute in (
            ("model_name", "model"),
            ("batch_size", "batchSize"),
            ("num_workers", "numWorkers"),
            ("epochs_completed", "epochsCompleted"),
            ("epochs_configured", "epochsConfigured"),
        ):
            value = run.get(key)
            if value is not None:
                run_element.set(attribute, str(value))
        add_metric(run_element, "best_val_mean_r2", run.get("best_val_mean_r2"))
        add_metric(run_element, "last_val_mean_r2", run.get("last_val_mean_r2"))
        add_metric(run_element, "last_val_loss", run.get("last_val_loss"))
        add_metric(run_element, "last_train_loss", run.get("last_train_loss"))
    return training_runs


def update_summary(summary: ET.Element, recommended_profile: dict | None, runs: list[dict]) -> None:
    current_task = summary.find("currentTask")
    if current_task is not None:
        current_task.set("status", "in_progress")

    overall_state = summary.find("overallState")
    if overall_state is None:
        overall_state = ET.SubElement(summary, "overallState")

    tracked_runs = sum(1 for run in runs if run.get("epochs_completed"))
    if recommended_profile is None:
        overall_state.text = "Training dataset is complete, training code is implemented, and profiling or run metadata has not been collected yet."
        return

    batch_size = recommended_profile.get("batch_size")
    num_workers = recommended_profile.get("num_workers")
    throughput = recommended_profile.get("images_per_sec_end_to_end")
    overall_state.text = (
        "Training dataset is complete, training code is implemented, and profiling shows the pipeline is GPU-bound on the ext4 drive. "
        f"Current recommended config is batch size {batch_size} with {num_workers} workers at about {throughput:.1f} images/sec; tracked training runs with epoch history: {tracked_runs}."
    )


def update_training_element(training: ET.Element, recommended_profile: dict | None) -> None:
    if recommended_profile is None:
        return

    recommended = training.find("recommendedConfig")
    if recommended is None:
        recommended = ET.SubElement(training, "recommendedConfig")
    recommended.set("batchSize", str(recommended_profile.get("batch_size")))
    recommended.set("numWorkers", str(recommended_profile.get("num_workers")))
    model_name = recommended_profile.get("model_name")
    if model_name:
        recommended.set("model", str(model_name))


def update_next_actions(next_actions: ET.Element, runs: list[dict], recommended_profile: dict | None) -> None:
    for child in list(next_actions):
        next_actions.remove(child)

    has_completed_run = any(
        run.get("epochs_completed") and run["kind"] in ("train", "real") for run in runs
    )
    batch_size = (recommended_profile or {}).get("batch_size", 128)
    num_workers = (recommended_profile or {}).get("num_workers", 8)

    action_texts = []
    if not has_completed_run:
        action_texts.append(("high", "pending", f"Start the first long-running DINOv2 climate training run with batch size {batch_size} and {num_workers} workers."))
    else:
        action_texts.append(("high", "pending", "Assess per-target validation R2 of completed runs and choose next experiment: morphology variants (SAM 3 segmentation) vs. scale-up (resolution/capacity)."))
    action_texts.extend(
        [
            ("high", "pending", "Monitor TensorBoard during training for loss stability and throughput."),
            ("medium", "pending", "Test whether a larger batch size remains stable over a sustained run if GPU memory allows."),
            ("medium", "pending", "Evaluate the strongest checkpoint and inspect validation R2 by target."),
            ("medium", "pending", "Adjust unfreeze depth or learning rates after the first sustained run if validation quality stalls."),
        ]
    )

    for priority, status, text in action_texts:
        action = ET.SubElement(next_actions, "action", priority=priority, status=status)
        action.text = text


def update_commands(commands: ET.Element, recommended_profile: dict | None) -> None:
    for child in list(commands):
        commands.remove(child)

    batch_size = (recommended_profile or {}).get("batch_size", 128)
    num_workers = (recommended_profile or {}).get("num_workers", 8)
    entries = {
        "profile": f"python scripts/training/profile_dinov2.py --mode all --batch-size {batch_size} --num-workers {num_workers}",
        "train": f"python scripts/training/train_dinov2.py --batch-size {batch_size} --num-workers {num_workers}",
        "tensorboard": "make tensorboard TENSORBOARD_LOGDIR=outputs/models/dinov2_climate/tensorboard",
        "progress": "python scripts/training/update_progress.py",
    }
    for name, text in entries.items():
        command = ET.SubElement(commands, "command", name=name)
        command.text = text


def ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def ensure_artifact(artifacts: ET.Element, path: str, status: str, purpose: str) -> None:
    for artifact in artifacts.findall("artifact"):
        if artifact.get("path") == path:
            artifact.set("status", status)
            artifact.set("purpose", purpose)
            return
    ET.SubElement(artifacts, "artifact", path=path, status=status, purpose=purpose)


def main() -> int:
    args = parse_args()

    tree = ET.parse(args.progress_path)
    root = tree.getroot()
    root.set("updated", str(date.today()))

    loader_profiles, train_profiles = discover_profiles(args.profiles_dir)
    recommended_profile = pick_recommended_profile(train_profiles, args.memory_baseline_gib)
    runs = discover_runs(args.models_dir)

    summary = ensure_child(root, "summary")
    update_summary(summary, recommended_profile, runs)

    artifacts = ensure_child(root, "artifacts")
    ensure_artifact(
        artifacts,
        path="scripts/training/update_progress.py",
        status="ready",
        purpose="Refresh PROGRESS.xml from profile outputs and training runs",
    )

    profiling = build_profiling_element(root.find("profiling"), loader_profiles, train_profiles, recommended_profile)
    replace_element(root, profiling)

    training = ensure_child(root, "training")
    update_training_element(training, recommended_profile)

    training_runs = build_training_runs_element(runs, args.max_runs)
    replace_element(root, training_runs)

    next_actions = ensure_child(root, "nextActions")
    update_next_actions(next_actions, runs, recommended_profile)

    commands = ensure_child(root, "commands")
    update_commands(commands, recommended_profile)

    ET.indent(tree, space="  ")
    tree.write(args.progress_path, encoding="UTF-8", xml_declaration=True)
    print(f"updated {args.progress_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
