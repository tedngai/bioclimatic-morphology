# Infrastructure: Two-Machine Setup

*Last verified: 2026-09-26*

The project runs on two machines connected over Tailscale. This machine is the **management hub**; the GPU server runs training. Use git as the sync channel.

## Machines

|  | Management (this machine) | GPU server (`spark-server`) |
|---|---|---|
| Hostname | `cio-tngai-m` | `promaxgb10-42ce` |
| OS / arch | Ubuntu 22.04, x86_64 | Ubuntu 24.04, aarch64 |
| GPU | RTX 2000 Ada Laptop, 8 GB | NVIDIA GB10 (Grace Blackwell), ~128 GB unified memory |
| Driver / CUDA | 591.55 | 580.159.03 / CUDA 13.0 |
| Repo path | `/home/tngai/data/bioclimatic-morphology` | `/mnt/wholemilk/bioclimatic-morphology` |
| Role | source of truth: edit code/docs, commit, push, data prep | DINOv2 training, evaluation, SAM 3 segmentation |
| Data | train CSVs + images (~102 GB) | train CSVs + images (~102 GB), model checkpoints |

The GB10 is a unified-memory machine: `nvidia-smi` reports total/used memory as `N/A`; use `nvidia-smi --query-compute-apps=used_memory` or `torch.cuda.mem_get_info()` for real numbers.

## SSH Access

Host alias is configured in `~/.ssh/config` on this machine:

```bash
ssh spark-server              # interactive (prompts for password)
ssh spark-server 'nvidia-smi' # one-off command
```

Authentication is **password-based** (user `tngai`) for now. For non-interactive/scripted use, two helpers exist on the management machine:

- `~/.ssh/spark-server.pass` — password, mode 600 (never commit)
- `~/.ssh/spark-askpass.sh` — prints the password for OpenSSH askpass

Non-interactive pattern (OpenSSH ≥ 8.4):

```bash
SSH_ASKPASS="$HOME/.ssh/spark-askpass.sh" SSH_ASKPASS_REQUIRE=force \
  ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no spark-server 'command'
```

*Recommendation:* switch to SSH keys when convenient (`ssh-keygen -t ed25519`, add the public key to the server's `~/.ssh/authorized_keys`), then delete `spark-server.pass` and add `IdentityFile` to `~/.ssh/config`.

## Git Workflow (the sync channel)

Both machines push/pull over HTTPS. Authentication uses `GITHUB_PAT` from each machine's `.env` via a credential helper at `~/.local/bin/github-token-helper` (git remote URLs are tokenless — do not put tokens back into URLs).

- If the PAT is rotated, update `.env` on **both** machines only.
- `data/**` and `outputs/**` are gitignored (large/regenerable). Code, docs, configs, `PROGRESS.xml`, small run logs and epoch `history.csv` files are tracked.
- Checkpoints (`*.pt`, ~550 MB each) live only on the server under `outputs/models/`.

Canonical loop:

```bash
# 1. Edit/commit/push here (management machine)
git add -A && git commit -m "..." && git push origin main

# 2. Update the server and run a job there
make remote-pull                       # or: ssh spark-server 'cd /mnt/wholemilk/bioclimatic-morphology && git pull --ff-only'
make remote-status                     # inspect git/GPU/disk/tmux
ssh spark-server                       # then: tmux new -s train; run training

# 3. Bring results back
#    - small artifacts (logs, history.csv, PROGRESS.xml): commit them on whichever side produced them
#    - big artifacts (checkpoints): scp/rsync if needed, e.g.
#      rsync -av spark-server:/mnt/wholemilk/bioclimatic-morphology/outputs/models/<run>/ ./
```

`make remote-shell`, `make remote-status`, `make remote-pull` are defined in the `Makefile` (override with `REMOTE_HOST=` / `REMOTE_DIR=`).

## Server Environments

| Env | Python | Packages | Use |
|---|---|---|---|
| `bm-venv` | 3.11.15 | torch 2.12.0+cu130, torchvision, transformers 5.8.1 | DINOv2 training, evaluation, profiling |
| `sam3` | 3.11 | torch 2.12.0+cu130, `sam3` (editable from `/mnt/wholemilk/sam3`), numpy 1.26.4 (`numpy<2`) | SAM 3 segmentation |

- Paths: `/home/tngai/miniconda3/envs/bm-venv/bin/python`, `/home/tngai/miniconda3/envs/sam3/bin/python`.
- The repo `.venv` on the server is **not** usable for GPU work; system `python3.12` has torch but belongs to other services — don't use it.
- SAM 3 repo/checkpoint: `/mnt/wholemilk/sam3` with local `sam3.pt` (3.3 GB). The HF repo `facebook/sam3` is gated and the cached token lacks access (HTTP 401), so pass `--checkpoint /mnt/wholemilk/sam3/sam3.pt` to avoid HF entirely.

## GPU Sharing (read before launching training)

A `sglang` server for an LLM (`Qwen3.8-27B`, root-owned, port 8000) runs continuously on the GB10 and holds **~99 GiB** of the ~128 GB unified memory. DINOv2 ViT-B training peaks at ~5.4 GiB (bs=128), so it can coexist, but:

- Always check `nvidia-smi` first and confirm free memory.
- Large experiments (ViT-L/14, image_size 518, big batches) need the sglang service scaled down or stopped.
- Long jobs go in `tmux` (a session named `0` already exists); TensorBoard binds `0.0.0.0:6006` via `make tensorboard` — tunnel with `ssh -L 6006:localhost:6006 spark-server`.

## Disk

| Mount | Size | Used | Free |
|---|---|---|---|
| `/mnt/wholemilk` (server) | 458 GB ext4 | 219 GB | 216 GB |
| `/` nvme (server) | 925 GB | 268 GB | 611 GB |

Images: mammals 56 GB + birds 46 GB. Checkpoints ~550 MB each; prune stale runs with `rm -rf outputs/models/<run>` when needed.

## Known Gotchas

- **Password auth prompts break scripts.** Use the askpass pattern above or switch to keys.
- **Checkpoints store absolute paths** from the machine that wrote them. On the server, `evaluate.py` needs `--csv-path data/vision/train_all.csv` because older checkpoints reference a stale mount path.
- **`--csv-path` / image paths are relative to the repo root** on the machine running the job.
- **The old GitHub PAT embedded in remote URLs is dead** (401). Historical git configs may still contain it — rotate/remove anywhere it appears outside `.env`.
- **SAM 3 pilot failure (2026-06-28).** All 1000 images failed with `forward:Expected grad to be disabled` from `sam3/perflib/fused.py`. Root cause verified on torch 2.12: `segment_sam3.py` calls `torch.inference_mode().__enter__()` on a temporary object, which is garbage-collected immediately, leaving grad enabled. Fix by wrapping model build + inference loop in a proper `with torch.inference_mode():` block (or `torch.set_grad_enabled(False)`), then rerun with `--checkpoint`.

## Related Docs

- `AGENTS.md` — current task state and next actions
- `project_scope.md` — project-level status checklist
- `docs/phase8_vision.md` — Phase 8 implementation plan (pre-implementation; see AGENTS.md for actual status)
